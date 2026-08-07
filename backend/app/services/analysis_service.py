"""
Analiz Orkestrasyon Servisi (Analysis Service).

Bu servis tüm mühendislik çekirdek modüllerini (CLT, MeshEngine, BearingModel, 
FEMSolver, FailureCriteriaEngine) uçtan uca senkron bir akışta birleştirir.
"""
import numpy as np
import time
from typing import Dict, Any

from ..core.materials_db import MaterialsDB
from ..core.clt import Ply, Laminate, CLTEngine
from ..core.mesh_engine import MeshEngine, GeometryConfig, HAS_GMSH
from ..core.bearing import BearingPressureModel, BearingLoad
from ..core.fem_solver import FEMSolver, MeshData
from ..core.failure import FailureCriteriaEngine


class AnalysisService:
    """Kompozit Bağlantı Analiz Servisi."""

    def __init__(self, materials_db_path: str = None):
        self.materials_db = MaterialsDB(materials_db_path)
        self.clt_engine = CLTEngine()
        self.failure_engine = FailureCriteriaEngine()
        self.bearing_model = BearingPressureModel()

    def run_full_analysis(self, request_data: dict) -> dict:
        t_start = time.perf_counter()

        # 1. Malzeme ve Katman Yapısını Oluştur
        plies_data = request_data.get('plies', [])
        if not plies_data:
            raise ValueError("En az 1 katman (ply) tanımlanmalıdır.")

        plies = []
        for idx, ply_in in enumerate(plies_data):
            mat_id = ply_in['material_id']
            mat = self.materials_db.get_material(mat_id)
            angle = float(ply_in['angle'])
            thickness = float(ply_in.get('thickness', mat.E1)) if 'thickness' not in ply_in else float(ply_in['thickness'])
            plies.append(Ply(material=mat, angle=angle, thickness=thickness, ply_id=idx))

        laminate = Laminate(plies=plies)
        A, B, D = self.clt_engine.compute_ABD(laminate)
        B_nonzero = not np.allclose(B, 0, atol=1e-5)

        # 2. Mesh Oluştur (Gmsh mevcut ise Gmsh, yoksa Parametrik Grid Fallback)
        width = float(request_data.get('width', 200.0))
        height = float(request_data.get('height', 100.0))
        holes_in = request_data.get('holes', [])
        mesh_size_global = float(request_data.get('mesh_size_global', 10.0))
        mesh_size_hole = float(request_data.get('mesh_size_hole', 2.0))

        geo_config = GeometryConfig(
            width=width,
            height=height,
            holes=holes_in,
            mesh_size_global=mesh_size_global,
            mesh_size_hole=mesh_size_hole
        )

        if HAS_GMSH:
            mesh_engine = MeshEngine()
            raw_mesh = mesh_engine.create_mesh(geo_config)
            mesh_data = MeshData(
                nodes=raw_mesh['nodes'],
                elements=raw_mesh['elements'],
                element_type=raw_mesh['element_type'],
                boundary_nodes=raw_mesh['boundary_nodes'],
                hole_boundary_nodes=raw_mesh['hole_boundary_nodes']
            )
            mesh_stats = raw_mesh['statistics']
        else:
            # Simple Parametric Quad Grid Fallback (Gmsh olmadan da çalışabilirlik)
            mesh_data, mesh_stats = self._create_fallback_grid(width, height, mesh_size_global)

        # 3. Yükler ve Sınır Koşulları
        nodal_forces = {}
        total_applied_load = 0.0

        for h_idx, hole_in in enumerate(holes_in):
            load_mag = float(hole_in.get('load_magnitude', 0.0))
            if load_mag > 0 and h_idx < len(mesh_data.hole_boundary_nodes):
                total_applied_load += load_mag
                b_load = BearingLoad(
                    hole_x=float(hole_in['x']),
                    hole_y=float(hole_in['y']),
                    diameter=float(hole_in['diameter']),
                    load_magnitude=load_mag,
                    load_angle=float(hole_in.get('load_angle', 0.0))
                )
                h_nodes = mesh_data.hole_boundary_nodes[h_idx].get('nodes', [])
                if h_nodes:
                    hole_forces = self.bearing_model.apply_bearing_loads(
                        b_load, h_nodes, laminate.total_thickness
                    )
                    nodal_forces.update(hole_forces)

        # Eğer hiç yatak yükü verilmediyse plaka sağ kenarına düzgün çekme yükü uygula (default test case)
        if total_applied_load == 0.0:
            right_nodes = mesh_data.boundary_nodes.get('right', [])
            if right_nodes:
                force_per_node = 1000.0 / max(len(right_nodes), 1)
                for nid in right_nodes:
                    nodal_forces[nid] = (force_per_node, 0.0)
                total_applied_load = 1000.0

        # Sol kenar sabitleme (Fixed Boundary Condition)
        fixed_nodes = mesh_data.boundary_nodes.get('left', [0, 1])

        # 4. FEM Çözümü (spsolve)
        fem_solver = FEMSolver(laminate=laminate)
        fem_result = fem_solver.solve(
            mesh=mesh_data,
            nodal_forces=nodal_forces,
            fixed_nodes=fixed_nodes,
            constraint_type=request_data.get('constraint_type', 'fixed')
        )

        # 5. Katman Bazlı Kırılma ve MoS Değerlendirmesi
        ply_results = []
        min_mos = float('inf')
        critical_ply_id = 0
        critical_angle = 0.0
        critical_mode = "None"
        governing_criterion = "Hashin"

        for ply_idx, ply in enumerate(laminate.plies):
            ply_stresses_local = fem_result.ply_stresses[ply_idx]['nodal_stresses_local']
            
            # En kritik düğümü bul
            max_fi_ply = 0.0
            crit_eval = None

            for stress_vec in ply_stresses_local:
                s1, s2, t12 = stress_vec[0], stress_vec[1], stress_vec[2]
                eval_res = self.failure_engine.evaluate_ply(s1, s2, t12, ply.material, ply_idx, ply.angle)
                if eval_res.hashin_max_fi >= max_fi_ply:
                    max_fi_ply = eval_res.hashin_max_fi
                    crit_eval = eval_res

            if crit_eval is None:
                crit_eval = self.failure_engine.evaluate_ply(0, 0, 0, ply.material, ply_idx, ply.angle)

            ply_results.append({
                'ply_id': ply_idx,
                'angle': ply.angle,
                'hashin_max_fi': float(crit_eval.hashin_max_fi),
                'dominant_mode': crit_eval.hashin_failure_mode,
                'tsai_wu_fi': float(crit_eval.tsai_wu_fi),
                'mos_hashin': float(crit_eval.mos_hashin),
                'is_failed': bool(crit_eval.is_failed)
            })

            if crit_eval.mos_hashin < min_mos:
                min_mos = crit_eval.mos_hashin
                critical_ply_id = ply_idx
                critical_angle = ply.angle
                critical_mode = crit_eval.hashin_failure_mode
                governing_criterion = crit_eval.governing_criterion

        overall_status = "PASS" if min_mos >= 0.0 else "FAIL"
        t_end = time.perf_counter()

        return {
            'layup_notation': laminate.layup_notation,
            'total_thickness': float(laminate.total_thickness),
            'min_mos': float(min_mos) if min_mos != float('inf') else 999.0,
            'overall_status': overall_status,
            'governing_criterion': governing_criterion,
            'critical_ply': critical_ply_id,
            'critical_angle': critical_angle,
            'critical_mode': critical_mode,
            'ply_results': ply_results,
            'A_matrix': A.tolist(),
            'B_matrix': B.tolist(),
            'D_matrix': D.tolist(),
            'B_nonzero': B_nonzero,
            'applied_load': total_applied_load,
            'computation_time_ms': (t_end - t_start) * 1000.0,
            'mesh_summary': mesh_stats,
            'nodes': mesh_data.nodes.tolist(),
            'elements': mesh_data.elements.tolist(),
            'nodal_stresses': fem_result.nodal_stresses.tolist()
        }

    def _create_fallback_grid(self, width: float, height: float, mesh_size: float):
        """Gmsh yüklü değilse devreye giren basit izoparametrik Q4 ağ üreteci."""
        nx = max(int(width / mesh_size), 4)
        ny = max(int(height / mesh_size), 2)

        x = np.linspace(0, width, nx + 1)
        y = np.linspace(0, height, ny + 1)
        xv, yv = np.meshgrid(x, y)

        nodes = np.column_stack([xv.ravel(), yv.ravel()])

        elements = []
        for j in range(ny):
            for i in range(nx):
                n1 = j * (nx + 1) + i
                n2 = j * (nx + 1) + i + 1
                n3 = (j + 1) * (nx + 1) + i + 1
                n4 = (j + 1) * (nx + 1) + i
                elements.append([n1, n2, n3, n4])

        elements = np.array(elements)

        tol = 1e-5
        boundary = {'left': [], 'right': [], 'bottom': [], 'top': [], 'holes': []}
        for idx, (nx_val, ny_val) in enumerate(nodes):
            if abs(nx_val) < tol: boundary['left'].append(idx)
            if abs(nx_val - width) < tol: boundary['right'].append(idx)
            if abs(ny_val) < tol: boundary['bottom'].append(idx)
            if abs(ny_val - height) < tol: boundary['top'].append(idx)

        mesh_data = MeshData(
            nodes=nodes,
            elements=elements,
            element_type='Q4',
            boundary_nodes=boundary,
            hole_boundary_nodes=[]
        )
        stats = {
            'n_nodes': len(nodes), 'n_elements': len(elements),
            'n_dof': 2 * len(nodes), 'element_type': 'Q4 (Fallback Grid)'
        }
        return mesh_data, stats
