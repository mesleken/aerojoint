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
    """Adım Adım İleri Düzey Kopma Çözücüsü."""

    def __init__(self, laminate: Laminate):
        self.laminate = laminate
        self.clt_engine = CLTEngine()
        self.failure_engine = FailureCriteriaEngine()
        self.fem_solver = FEMSolver(laminate)

    def run_pdm(self, mesh: MeshData, nodal_forces: Dict[int, List[float]], 
                fixed_nodes: List[int], total_applied_load: float, constraint_type: str = 'fixed',
                num_steps: int = 20) -> Dict[str, Any]:
        """
        Artırımlı Yükleme (Incremental Loading) ve Hasar Yayılım Çözümü.
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

        # Her adım için yük faktörü (0.2, 0.4, 0.6, 0.8, 1.0, vb.)
        load_factors = np.linspace(0.2, 1.0, num_steps)

        for step_idx, factor in enumerate(load_factors):
            current_forces = {
                nid: [fx * factor, fy * factor]
                for nid, (fx, fy) in nodal_forces.items()
            }
            current_applied_load = total_base_force * factor

            converged = False
            max_inner_iters = 4
            inner_iter = 0

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
                except Exception:
                    # Matris singüler olduysa yapı çökmüştür (Ultimate failure)
                    is_ultimate_failed = True
                    break

                u_full = np.zeros(n_dof)
                u_full[free_dofs] = u_free

                # 3 & 4. Gerilmeleri Eleman Bazında Hesapla ve Katman Katman Hashin Kontrolü Yap
                new_damage = False
                
                # Görselleştirme için nodal stress'leri oluştur (animasyon karesi için)
                # Orijinal C_eff'yi kullanarak yaklaşık stress çıkarıyoruz
                elem_stresses = self.fem_solver._compute_element_stresses(mesh, u_full)
                nodal_stresses = self.fem_solver._extrapolate_to_nodes(mesh, elem_stresses)
                stress_frames.append(nodal_stresses.copy())

                for elem_idx, elem_nodes in enumerate(mesh.elements):
                    xe = mesh.nodes[elem_nodes, 0]
                    ye = mesh.nodes[elem_nodes, 1]
                    dofs = []
                    for ni in elem_nodes:
                        dofs.extend([2*ni, 2*ni+1])
                    ue = u_full[dofs]

                    # Merkez noktadaki strain'i (şekil değiştirme) hesapla
                    dN = Q4Element.shape_function_derivatives(0.0, 0.0)
                    J = dN @ np.column_stack([xe, ye])
                    dN_dxy = np.linalg.inv(J) @ dN
                    
                    B = np.zeros((3, 8))
                    for i in range(4):
                        B[0, 2*i]     = dN_dxy[0, i]
                        B[1, 2*i + 1] = dN_dxy[1, i]
                        B[2, 2*i]     = dN_dxy[1, i]
                        B[2, 2*i + 1] = dN_dxy[0, i]
                        
                    epsilon = B @ ue

                    for ply_idx, ply in enumerate(self.laminate.plies):
                        has_mat_dmg = damage_state[elem_idx, ply_idx, 0]
                        has_fib_dmg = damage_state[elem_idx, ply_idx, 1]

                        # Zayıflatılmış (veya hasarsız) katman stiffness'ı
                        mat = ply.material
                        E1 = mat.E1 * (0.01 if has_fib_dmg else 1.0)
                        E2 = mat.E2 * (0.01 if has_fib_dmg else (0.1 if has_mat_dmg else 1.0))
                        G12 = mat.G12 * (0.01 if has_fib_dmg else (0.2 if has_mat_dmg else 1.0))
                        nu12 = mat.nu12
                        
                        nu21 = nu12 * E2 / E1
                        denom = max(1e-9, 1.0 - nu12 * nu21)
                        Q11 = E1 / denom
                        Q22 = E2 / denom
                        Q12 = nu12 * E2 / denom
                        Q66 = G12
                        Q = np.array([[Q11, Q12, 0.0], [Q12, Q22, 0.0], [0.0, 0.0, Q66]])

                        rad = np.radians(ply.angle)
                        m, n = np.cos(rad), np.sin(rad)
                        T = np.array([
                            [m**2, n**2, 2*m*n],
                            [n**2, m**2, -2*m*n],
                            [-m*n, m*n, m**2 - n**2]
                        ])
                        T_inv = np.linalg.inv(T)
                        
                        # Global stress -> Local stress
                        Qbar = T_inv @ Q @ T_inv.T
                        sg = Qbar @ epsilon
                        sl = T @ sg
                        
                        s1, s2, t12 = sl[0], sl[1], sl[2]

                        # Hashin Hasar Kriteri (thermal stres 0 olarak geçilir)
                        hashin = self.failure_engine.hashin_criteria([s1, s2, t12], [0.0, 0.0, 0.0], ply.material)

                        if (hashin['matrix_tension'] >= 1.0 or hashin['matrix_compression'] >= 1.0) and not damage_state[elem_idx, ply_idx, 0]:
                            damage_state[elem_idx, ply_idx, 0] = True
                            new_damage = True
                            if first_ply_failure_load == 0.0:
                                first_ply_failure_load = current_applied_load

                        if (hashin['fiber_tension'] >= 1.0 or hashin['fiber_compression'] >= 1.0) and not damage_state[elem_idx, ply_idx, 1]:
                            damage_state[elem_idx, ply_idx, 1] = True
                            new_damage = True

                if not new_damage:
                    converged = True

            matrix_failed_count = int(np.sum(damage_state[:, :, 0]))
            fiber_failed_count = int(np.sum(damage_state[:, :, 1]))

            if fiber_failed_count > (n_elements * n_plies * 0.5):
                is_ultimate_failed = True

            history.append(PDMStepResult(
                step=step_idx + 1,
                load_factor=float(factor),
                applied_load=float(current_applied_load),
                failed_matrix_count=matrix_failed_count,
                failed_fiber_count=fiber_failed_count,
                status="CRITICAL_DAMAGE" if is_ultimate_failed else ("DAMAGE_PROPAGATING" if matrix_failed_count > 0 else "STABLE")
            ))

            if not is_ultimate_failed:
                ultimate_load = current_applied_load

            if is_ultimate_failed:
                break

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

        rows, cols, vals = [], [], []

        for elem_idx, elem_nodes in enumerate(mesh.elements):
            # Elemanın efektif A matrisini katman katman hesapla
            A_elem = np.zeros((3, 3))
            
            for ply_idx, ply in enumerate(self.laminate.plies):
                has_mat_dmg = damage_state[elem_idx, ply_idx, 0]
                has_fib_dmg = damage_state[elem_idx, ply_idx, 1]

                # Orijinal malzeme özellikleri
                mat = ply.material
                E1 = mat.E1
                E2 = mat.E2
                G12 = mat.G12
                nu12 = mat.nu12

                # Zayıflatma Kuralları (Stiffness Degradation Rules)
                if has_fib_dmg:
                    E1 *= 0.01
                    E2 *= 0.01
                    G12 *= 0.01
                elif has_mat_dmg:
                    E2 *= 0.1
                    G12 *= 0.2

                nu21 = nu12 * E2 / E1
                denom = max(1e-9, 1.0 - nu12 * nu21)
                
                Q11 = E1 / denom
                Q22 = E2 / denom
                Q12 = nu12 * E2 / denom
                Q66 = G12

                Q = np.array([[Q11, Q12, 0.0], [Q12, Q22, 0.0], [0.0, 0.0, Q66]])
                
                # Dönüştürülmüş Q̄ matrisi
                rad = np.radians(ply.angle)
                m, n = np.cos(rad), np.sin(rad)
                T = np.array([
                    [m**2, n**2, 2*m*n],
                    [n**2, m**2, -2*m*n],
                    [-m*n, m*n, m**2 - n**2]
                ])
                T_inv = np.linalg.inv(T)
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
                    rows.append(i_g)
                    cols.append(j_g)
                    vals.append(Ke[i_l, j_l])

        K = sparse.coo_matrix((vals, (rows, cols)), shape=(n_dof, n_dof))
        return K.tocsr()
