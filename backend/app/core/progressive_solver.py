"""
İleri Düzey Kopma Analizi Motoru (Progressive Damage Modeling - PDM).

Bu modül, ilk katman çatlamasından (First-Ply Failure) nihai göçmeye (Ultimate Failure)
kadar yük adımlarını koşturur ve malzeme özelliğini katman/eleman bazında düşürür (Stiffness Degradation).
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from dataclasses import dataclass
from typing import Dict, List, Any
from .clt import Laminate, OrthotropicMaterial, CLTEngine
from .fem_elements import Q4Element
from .fem_solver import MeshData, FEMResult, FEMSolver
from .failure import FailureCriteriaEngine


@dataclass
class PDMStepResult:
    step: int
    load_factor: float
    applied_load: float
    failed_matrix_count: int
    failed_fiber_count: int
    status: str


class ProgressiveDamageSolver:
    """Adım Adım İleri Düzey Kopma Çözücüsü (Progressive Damage Modeling - PDM)."""

    def __init__(self, laminate: Laminate):
        self.laminate = laminate
        self.clt_engine = CLTEngine()
        self.failure_engine = FailureCriteriaEngine()
        self.fem_solver = FEMSolver(laminate)
        
        # Dönüşüm matrislerini önceden hesapla (Performans Optimizasyonu)
        self.T_matrices = []
        self.T_inv_matrices = []
        for ply in laminate.plies:
            rad = np.radians(ply.angle)
            m, n = np.cos(rad), np.sin(rad)
            T = np.array([
                [m**2, n**2, 2*m*n],
                [n**2, m**2, -2*m*n],
                [-m*n, m*n, m**2 - n**2]
            ])
            # T^{-1}(θ) = T(-θ)
            rad_neg = np.radians(-ply.angle)
            m_n, n_n = np.cos(rad_neg), np.sin(rad_neg)
            T_inv = np.array([
                [m_n**2, n_n**2, 2*m_n*n_n],
                [n_n**2, m_n**2, -2*m_n*n_n],
                [-m_n*n_n, m_n*n_n, m_n**2 - n_n**2]
            ])
            self.T_matrices.append(T)
            self.T_inv_matrices.append(T_inv)

    def run_pdm(self, mesh: MeshData, nodal_forces: Dict[int, List[float]], 
                fixed_nodes: List[int], total_applied_load: float, constraint_type: str = 'fixed',
                num_steps: int = 25) -> Dict[str, Any]:
        """
        Adaptif Artırımlı Yükleme (Adaptive Incremental Loading) ve Hasar Yayılım Çözümü.
        Sabit tavan kullanılmaz; nihai göçme (Ultimate Failure) gerçekleşene kadar yük adaptif olarak artırılır.
        """
        n_elements = len(mesh.elements)
        n_plies = len(self.laminate.plies)

        # Hasar Durumu Dizileri [element_idx, ply_idx, mode]
        # mode: 0 -> Matrix Damage, 1 -> Fiber Damage
        damage_state = np.zeros((n_elements, n_plies, 2), dtype=bool)

        history: List[PDMStepResult] = []
        stress_frames: List[np.ndarray] = []

        total_base_force = total_applied_load
        
        first_ply_failure_load = 0.0
        ultimate_load = 0.0
        is_ultimate_failed = False

        # ADAPTİF YÜK TARAMA: Göçme gerçekleşene kadar yük adım adım artırılır
        factor = 0.2
        step_increment = 0.1
        max_search_factor = 10.0 # Maksimum 10 katına kadar adaptif arama
        step_idx = 0

        while not is_ultimate_failed and factor <= max_search_factor:
            step_idx += 1
            current_forces = {
                nid: [fx * factor, fy * factor]
                for nid, (fx, fy) in nodal_forces.items()
            }
            current_applied_load = total_base_force * factor

            converged = False
            max_inner_iters = 5
            inner_iter = 0
            u_full = None

            while not converged and inner_iter < max_inner_iters:
                inner_iter += 1

                # 1. Hasarlı duruma göre Eşdeğer Katman Rijitliği Matrisi Montajı
                K_global = self._assemble_degraded_stiffness(mesh, damage_state)
                F = self.fem_solver.create_force_vector(mesh, current_forces)

                # 2. Sınır koşulları & Çözüm
                n_dof = K_global.shape[0]
                fixed_dofs = set()
                for node_id in fixed_nodes:
                    if constraint_type == 'fixed':
                        fixed_dofs.update([2 * node_id, 2 * node_id + 1])
                    elif constraint_type == 'roller_x':
                        fixed_dofs.add(2 * node_id + 1)
                    elif constraint_type == 'roller_y':
                        fixed_dofs.add(2 * node_id)

                free_dofs = np.setdiff1d(np.arange(n_dof), sorted(fixed_dofs))

                try:
                    K_ff = K_global[np.ix_(free_dofs, free_dofs)]
                    F_f = F[free_dofs]
                    u_free = spsolve(K_ff, F_f)
                    
                    # Fiziksel yapay göçme tespiti (Deformasyon > 50 mm ise yapı stabilitesini yitirmiştir)
                    if np.max(np.abs(u_free)) > 50.0:
                        is_ultimate_failed = True
                        break
                except Exception:
                    # Matris singüler olduysa yapı fiziksel olarak taşımayı bırakmıştır (Kopma)
                    is_ultimate_failed = True
                    break

                u_full = np.zeros(n_dof)
                u_full[free_dofs] = u_free

                # 3 & 4. 4 Gauss Noktasında Gerilme ve Katman Katman Hashin Kontrolü Yap
                new_damage = False

                for elem_idx, elem_nodes in enumerate(mesh.elements):
                    xe = mesh.nodes[elem_nodes, 0]
                    ye = mesh.nodes[elem_nodes, 1]
                    dofs = []
                    for ni in elem_nodes:
                        dofs.extend([2*ni, 2*ni+1])
                    ue = u_full[dofs]

                    # 4 Gauss Noktasında Gerinimi Oku (Hassas Pik Tespiti)
                    gauss_strains = []
                    for (xi, eta) in Q4Element.GAUSS_POINTS:
                        dN = Q4Element.shape_function_derivatives(xi, eta)
                        J = dN @ np.column_stack([xe, ye])
                        dN_dxy = np.linalg.inv(J) @ dN
                        
                        B = np.zeros((3, 8))
                        for i in range(4):
                            B[0, 2*i]     = dN_dxy[0, i]
                            B[1, 2*i + 1] = dN_dxy[1, i]
                            B[2, 2*i]     = dN_dxy[1, i]
                            B[2, 2*i + 1] = dN_dxy[0, i]
                        gauss_strains.append(B @ ue)

                    for ply_idx, ply in enumerate(self.laminate.plies):
                        has_mat_dmg = damage_state[elem_idx, ply_idx, 0]
                        has_fib_dmg = damage_state[elem_idx, ply_idx, 1]

                        # Zayıflatılmış malzeme özellikleri
                        mat = ply.material
                        E1 = mat.E1 * (0.01 if has_fib_dmg else 1.0)
                        E2 = mat.E2 * (0.01 if has_fib_dmg else (0.1 if has_mat_dmg else 1.0))
                        G12 = mat.G12 * (0.01 if has_fib_dmg else (0.2 if has_mat_dmg else 1.0))
                        nu12 = mat.nu12
                        
                        nu21 = nu12 * E2 / E1
                        denom = max(1e-9, 1.0 - nu12 * nu21)
                        Q = np.array([
                            [E1 / denom, nu12 * E2 / denom, 0.0],
                            [nu12 * E2 / denom, E2 / denom, 0.0],
                            [0.0, 0.0, G12]
                        ])

                        T = self.T_matrices[ply_idx]
                        T_inv = self.T_inv_matrices[ply_idx]
                        Qbar = T_inv @ Q @ T_inv.T

                        # 4 Gauss Noktasının En Kritik Hasar İndeksini (max(FI), NOT mean) Bul
                        max_hashin_mat = 0.0
                        max_hashin_fib = 0.0

                        for eps in gauss_strains:
                            sg = Qbar @ eps
                            sl = T @ sg
                            s1, s2, t12 = sl[0], sl[1], sl[2]
                            h_res = self.failure_engine.hashin_criteria([s1, s2, t12], [0.0, 0.0, 0.0], ply.material)
                            
                            mat_fi = max(h_res['matrix_tension'], h_res['matrix_compression'])
                            fib_fi = max(h_res['fiber_tension'], h_res['fiber_compression'])
                            if mat_fi > max_hashin_mat: max_hashin_mat = mat_fi
                            if fib_fi > max_hashin_fib: max_hashin_fib = fib_fi

                        if max_hashin_mat >= 1.0 and not damage_state[elem_idx, ply_idx, 0]:
                            damage_state[elem_idx, ply_idx, 0] = True
                            new_damage = True
                            if first_ply_failure_load == 0.0:
                                first_ply_failure_load = current_applied_load

                        if max_hashin_fib >= 1.0 and not damage_state[elem_idx, ply_idx, 1]:
                            damage_state[elem_idx, ply_idx, 1] = True
                            new_damage = True

                if not new_damage:
                    converged = True

            if is_ultimate_failed:
                break

            # SADECE Dış Yük Adımı Yakınsadığında Tek Bir Animasyon Karesi Sakla
            if u_full is not None:
                elem_stresses = self.fem_solver._compute_element_stresses(mesh, u_full)
                nodal_stresses, _ = self.fem_solver._extrapolate_to_nodes(mesh, elem_stresses)
                stress_frames.append(nodal_stresses.copy())

            matrix_failed_count = int(np.sum(damage_state[:, :, 0]))
            fiber_failed_count = int(np.sum(damage_state[:, :, 1]))

            # ADAPTİF ADIM DARALTMA (Adaptive Step Refinement):
            # Hasar henüz başlamadıysa hızlı adımla (0.10), hasar başladığında %2 hassasiyete (0.02) daralt
            if matrix_failed_count > 0 or fiber_failed_count > 0:
                step_increment = 0.02
            else:
                step_increment = 0.10

            history.append(PDMStepResult(
                step=step_idx,
                load_factor=float(factor),
                applied_load=float(current_applied_load),
                failed_matrix_count=matrix_failed_count,
                failed_fiber_count=fiber_failed_count,
                status="CRITICAL_DAMAGE" if is_ultimate_failed else ("DAMAGE_PROPAGATING" if matrix_failed_count > 0 else "STABLE")
            ))

            if not is_ultimate_failed:
                ultimate_load = current_applied_load

            factor += step_increment

        if first_ply_failure_load == 0.0:
            first_ply_failure_load = total_base_force

        return {
            'ultimate_load_N': float(ultimate_load if ultimate_load > 0 else total_base_force),
            'first_ply_failure_load_N': float(first_ply_failure_load),
            'history': [h.__dict__ for h in history],
            'is_ultimate_failed': bool(is_ultimate_failed),
            'stress_frames': [sf.tolist() for sf in stress_frames]
        }

    def _assemble_degraded_stiffness(self, mesh: MeshData, damage_state: np.ndarray) -> sparse.csr_matrix:
        """Hasar durumuna göre malzeme özelliklerini zayıflatarak global K matrisini oluşturur."""
        n_nodes = len(mesh.nodes)
        n_dof = 2 * n_nodes
        thickness = self.laminate.total_thickness

        n_elems = len(mesh.elements)
        total_entries = n_elems * 64
        rows = np.zeros(total_entries, dtype=int)
        cols = np.zeros(total_entries, dtype=int)
        vals = np.zeros(total_entries, dtype=float)

        ptr = 0
        for elem_idx, elem_nodes in enumerate(mesh.elements):
            A_elem = np.zeros((3, 3))
            
            for ply_idx, ply in enumerate(self.laminate.plies):
                has_mat_dmg = damage_state[elem_idx, ply_idx, 0]
                has_fib_dmg = damage_state[elem_idx, ply_idx, 1]

                mat = ply.material
                E1 = mat.E1 * (0.01 if has_fib_dmg else 1.0)
                E2 = mat.E2 * (0.01 if has_fib_dmg else (0.1 if has_mat_dmg else 1.0))
                G12 = mat.G12 * (0.01 if has_fib_dmg else (0.2 if has_mat_dmg else 1.0))
                nu12 = mat.nu12

                nu21 = nu12 * E2 / E1
                denom = max(1e-9, 1.0 - nu12 * nu21)
                
                Q = np.array([
                    [E1 / denom, nu12 * E2 / denom, 0.0],
                    [nu12 * E2 / denom, E2 / denom, 0.0],
                    [0.0, 0.0, G12]
                ])
                
                T_inv = self.T_inv_matrices[ply_idx]
                Qbar = T_inv @ Q @ T_inv.T
                A_elem += Qbar * ply.thickness

            C_elem = A_elem / thickness

            xe = mesh.nodes[elem_nodes, 0]
            ye = mesh.nodes[elem_nodes, 1]
            Ke = Q4Element.stiffness_matrix(xe, ye, C_elem, thickness)

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
