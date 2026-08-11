"""
Ortotropik 2D Düzlem Gerilme FEM Çözücüsü.
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from dataclasses import dataclass
from .fem_elements import Q4Element
from .clt import CLTEngine, Laminate
import time

@dataclass
class MeshData:
    """Mesh verisi."""
    nodes: np.ndarray           # (N_nodes, 2)
    elements: np.ndarray        # (N_elements, 4) Q4 için
    element_type: str           # 'Q4'
    boundary_nodes: dict
    hole_boundary_nodes: list

@dataclass  
class FEMResult:
    """FEM çözüm sonuçları."""
    displacements: np.ndarray
    element_stresses: list
    nodal_stresses: np.ndarray              # Ortalanmış (Görselleştirme için)
    element_corner_stresses: np.ndarray     # Ortalanmamış (Konservatif kırılma hesabı için)
    ply_stresses: list                      # Katman gerilmeleri (Hem ortalanmış hem ortalanmamış)
    computation_time_ms: float


class FEMSolver:
    """Ortotropik 2D Düzlem Gerilme FEM Çözücüsü."""
    
    def __init__(self, laminate: Laminate):
        self.laminate = laminate
        self.clt_engine = CLTEngine()
        
        A, B, D = self.clt_engine.compute_ABD(laminate)
        h = laminate.total_thickness
        self.C_eff = A / h
        
        # Her katmanın Q̄ matrisi (gerilme geri hesabı için)
        self.Qbar_per_ply = []
        for ply in laminate.plies:
            Q = self.clt_engine.compute_Q(ply.material)
            Qbar = self.clt_engine.compute_Qbar(Q, ply.angle)
            self.Qbar_per_ply.append(Qbar)
    
    def assemble_global_stiffness(self, mesh: MeshData) -> sparse.csr_matrix:
        """Global K matrisini Vektörize Ön-Tahsisli COO → CSR sparse formatında montajla."""
        n_nodes = len(mesh.nodes)
        n_dof = 2 * n_nodes
        thickness = self.laminate.total_thickness
        
        n_elems = len(mesh.elements)
        # Her Q4 eleman 8x8 = 64 girdiye sahiptir
        total_entries = n_elems * 64
        rows = np.zeros(total_entries, dtype=int)
        cols = np.zeros(total_entries, dtype=int)
        vals = np.zeros(total_entries, dtype=float)
        
        ptr = 0
        for elem_nodes in mesh.elements:
            xe = mesh.nodes[elem_nodes, 0]
            ye = mesh.nodes[elem_nodes, 1]
            
            Ke = Q4Element.stiffness_matrix(xe, ye, self.C_eff, thickness)
            
            dofs = []
            for node_idx in elem_nodes:
                dofs.extend([2 * node_idx, 2 * node_idx + 1])
            
            for i_l, i_g in enumerate(dofs):
                for j_l, j_g in enumerate(dofs):
                    rows[ptr] = i_g
                    cols[ptr] = j_g
                    vals[ptr] = Ke[i_l, j_l]
                    ptr += 1
        
        K = sparse.coo_matrix((vals, (rows, cols)), shape=(n_dof, n_dof))
        return K.tocsr()
    
    def create_force_vector(self, mesh: MeshData, 
                             nodal_forces: dict) -> np.ndarray:
        """Global kuvvet vektörü."""
        n_dof = 2 * len(mesh.nodes)
        F = np.zeros(n_dof)
        for node_id, (fx, fy) in nodal_forces.items():
            F[2 * node_id] += fx
            F[2 * node_id + 1] += fy
        return F
    
    def solve(self, mesh: MeshData, nodal_forces: dict,
              fixed_nodes: list, constraint_type: str = 'fixed') -> FEMResult:
        """
        Ana çözüm: K montajı → F oluşturma → BC → spsolve → gerilme geri hesabı.
        """
        t_start = time.perf_counter()
        
        K = self.assemble_global_stiffness(mesh)
        F = self.create_force_vector(mesh, nodal_forces)
        
        # Sınır koşulları
        n_dof = K.shape[0]
        fixed_dofs = set()
        for node_id in fixed_nodes:
            if constraint_type == 'fixed':
                fixed_dofs.update([2*node_id, 2*node_id+1])
            elif constraint_type == 'roller_x':
                fixed_dofs.add(2*node_id + 1)
            elif constraint_type == 'roller_y':
                fixed_dofs.add(2*node_id)
        
        free_dofs = np.setdiff1d(np.arange(n_dof), sorted(fixed_dofs))
        
        # spsolve (SuperLU Direct)
        K_ff = K[np.ix_(free_dofs, free_dofs)]
        F_f = F[free_dofs]
        u_free = spsolve(K_ff, F_f)
        
        u_full = np.zeros(n_dof)
        u_full[free_dofs] = u_free
        displacements = u_full.reshape(-1, 2)
        
        # Gerilme geri hesabı
        element_stresses = self._compute_element_stresses(mesh, u_full)
        nodal_stresses, element_corner_stresses = self._extrapolate_to_nodes(mesh, element_stresses)
        
        # Kırılma hesabı için ORTALANMAMIŞ eleman köşe gerilmeleri kullanılır (Konservatif pik gerilmeler)
        ply_stresses = self._compute_ply_stresses(nodal_stresses, element_corner_stresses, mesh)
        
        t_end = time.perf_counter()
        
        return FEMResult(
            displacements=displacements,
            element_stresses=element_stresses,
            nodal_stresses=nodal_stresses,
            element_corner_stresses=element_corner_stresses,
            ply_stresses=ply_stresses,
            computation_time_ms=(t_end - t_start) * 1000
        )
    
    def _compute_element_stresses(self, mesh, u_full):
        stresses = []
        for elem_nodes in mesh.elements:
            xe = mesh.nodes[elem_nodes, 0]
            ye = mesh.nodes[elem_nodes, 1]
            dofs = []
            for ni in elem_nodes:
                dofs.extend([2*ni, 2*ni+1])
            ue = u_full[dofs]
            sigma = Q4Element.compute_stress(xe, ye, ue, self.C_eff)
            stresses.append(sigma)
        return stresses
    
    def _extrapolate_to_nodes(self, mesh, element_stresses):
        """
        Gauss noktalarında (±1/√3) hesaplanan gerilmeleri bilineer Q4 Ekstrapolasyon 
        matrisi ile düğümlere (±1) ekstrapole eder.
        Döndürür:
          1) nodal_averaged_stresses: (N_nodes, 3) - Görselleştirme amaçlı ortalanmış
          2) element_corner_stresses: (N_elements, 4, 3) - Ortalanmamış ham pik gerilmeler (Kırılma analizi için)
        """
        n_nodes = len(mesh.nodes)
        n_elems = len(mesh.elements)
        nodal_sum = np.zeros((n_nodes, 3))
        nodal_count = np.zeros(n_nodes)
        element_corner_stresses = np.zeros((n_elems, 4, 3))
        
        # 4 Gauss noktasından (4x3) 4 Düğüme (4x3) Ekstrapolasyon Matrisi (E_extrap)
        s3_2 = np.sqrt(3.0) / 2.0
        E_extrap = np.array([
            [1.0 + s3_2, -0.5, 1.0 - s3_2, -0.5],
            [-0.5, 1.0 + s3_2, -0.5, 1.0 - s3_2],
            [1.0 - s3_2, -0.5, 1.0 + s3_2, -0.5],
            [-0.5, 1.0 - s3_2, -0.5, 1.0 + s3_2]
        ])

        for elem_idx, elem_nodes in enumerate(mesh.elements):
            gauss_stresses = np.array(element_stresses[elem_idx]) # (4, 3)
            # Gauss noktalarından düğümlere ekstrapolasyon (Ortalanmamış)
            node_stresses_elem = E_extrap @ gauss_stresses # (4, 3)
            element_corner_stresses[elem_idx] = node_stresses_elem
            
            for local_idx, ni in enumerate(elem_nodes):
                nodal_sum[ni] += node_stresses_elem[local_idx]
                nodal_count[ni] += 1
                
        nodal_count[nodal_count == 0] = 1
        nodal_averaged = nodal_sum / nodal_count[:, np.newaxis]
        return nodal_averaged, element_corner_stresses
    
    def _compute_ply_stresses(self, nodal_stresses, element_corner_stresses, mesh):
        # Gerçek CLT Kinematiği: Global birleşik gerilmelerden -> Global gerinim (Strain) -> Katman bazlı gerilme (Stress)
        C_eff_inv = np.linalg.inv(self.C_eff)
        
        ply_results = []
        for ply_idx, ply in enumerate(self.laminate.plies):
            theta_rad = np.radians(ply.angle)
            m, n = np.cos(theta_rad), np.sin(theta_rad)
            T = np.array([
                [ m**2,  n**2,   2*m*n],
                [ n**2,  m**2,  -2*m*n],
                [-m*n,   m*n,    m**2 - n**2]
            ])
            
            Qbar = self.Qbar_per_ply[ply_idx]
            M_trans = Qbar @ C_eff_inv
            
            # 1. Ortalanmış Düğüm Gerilmeleri (Görselleştirme için)
            ply_nodal_global = np.array([M_trans @ sg for sg in nodal_stresses])
            ply_nodal_local = np.array([T @ sg for sg in ply_nodal_global])
            
            # 2. Ortalanmamış Eleman Köşe Gerilmeleri (Konservatif Kırılma Değerlendirmesi için)
            n_elems = len(element_corner_stresses)
            elem_corner_local = np.zeros((n_elems, 4, 3))
            for e_idx in range(n_elems):
                for c_idx in range(4):
                    sg_raw = element_corner_stresses[e_idx, c_idx]
                    sg_glob = M_trans @ sg_raw
                    elem_corner_local[e_idx, c_idx] = T @ sg_glob

            ply_results.append({
                'ply_id': ply_idx, 'angle': ply.angle,
                'nodal_stresses_local': ply_nodal_local,
                'nodal_stresses_global': ply_nodal_global,
                'elem_corner_stresses_local': elem_corner_local
            })
        return ply_results

