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
    nodal_stresses: np.ndarray
    ply_stresses: list
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
        """Global K matrisini COO → CSR sparse formatında montajla."""
        n_nodes = len(mesh.nodes)
        n_dof = 2 * n_nodes
        thickness = self.laminate.total_thickness
        
        rows, cols, vals = [], [], []
        
        for elem_nodes in mesh.elements:
            xe = mesh.nodes[elem_nodes, 0]
            ye = mesh.nodes[elem_nodes, 1]
            
            Ke = Q4Element.stiffness_matrix(xe, ye, self.C_eff, thickness)
            
            dofs = []
            for node_idx in elem_nodes:
                dofs.extend([2 * node_idx, 2 * node_idx + 1])
            
            for i_l, i_g in enumerate(dofs):
                for j_l, j_g in enumerate(dofs):
                    rows.append(i_g)
                    cols.append(j_g)
                    vals.append(Ke[i_l, j_l])
        
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
        nodal_stresses = self._extrapolate_to_nodes(mesh, element_stresses)
        ply_stresses = self._compute_ply_stresses(nodal_stresses)
        
        t_end = time.perf_counter()
        
        return FEMResult(
            displacements=displacements,
            element_stresses=element_stresses,
            nodal_stresses=nodal_stresses,
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
        n_nodes = len(mesh.nodes)
        nodal_sum = np.zeros((n_nodes, 3))
        nodal_count = np.zeros(n_nodes)
        for elem_idx, elem_nodes in enumerate(mesh.elements):
            elem_avg = np.mean(element_stresses[elem_idx], axis=0)
            for ni in elem_nodes:
                nodal_sum[ni] += elem_avg
                nodal_count[ni] += 1
        nodal_count[nodal_count == 0] = 1
        return nodal_sum / nodal_count[:, np.newaxis]
    
    def _compute_ply_stresses(self, nodal_stresses):
        ply_results = []
        for ply_idx, ply in enumerate(self.laminate.plies):
            theta_rad = np.radians(ply.angle)
            m, n = np.cos(theta_rad), np.sin(theta_rad)
            T = np.array([
                [ m**2,  n**2,   2*m*n],
                [ n**2,  m**2,  -2*m*n],
                [-m*n,   m*n,    m**2 - n**2]
            ])
            ply_nodal = np.array([T @ sg for sg in nodal_stresses])
            ply_results.append({
                'ply_id': ply_idx, 'angle': ply.angle,
                'nodal_stresses_local': ply_nodal,
                'nodal_stresses_global': nodal_stresses.copy()
            })
        return ply_results
