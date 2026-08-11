"""
AeroJoint V3.0 CAD & FEM Load Matcher Birebir Test Suite.
"""

import os
import json
import pytest
from app.core.cad_engine import CADEngine
from app.core.fem_load_matcher import FEMLoadMatcher

def test_cad_engine_mesh_and_holes():
    engine = CADEngine()
    mesh = engine._create_parametric_lug_mesh()
    assert mesh is not None
    
    holes = engine.detect_holes_from_mesh(mesh)
    assert isinstance(holes, list)
    print(f"✅ CAD Engine Mesh & Hole Detection Passed: {len(holes)} holes detected.")

def test_curvature_profiler_and_dcm():
    engine = CADEngine()
    mesh = engine._create_parametric_lug_mesh()
    curv = engine.analyze_surface_curvature(mesh)
    assert "recommended_option" in curv
    
    # DCM Direction Cosine Matrix test for normal (0, 0, 1)
    R = engine.compute_direction_cosine_matrix((0.0, 0.0, 1.0))
    assert R.shape == (3, 3)
    
    transformed = engine.transform_3d_force_to_2d_plane([1000.0, 500.0, 0.0], R)
    assert transformed["Fx_local"] == 1000.0
    assert transformed["Fy_local"] == 500.0
    print(f"✅ CAD Curvature Profiler & DCM Matrix Transformation Passed.")

def test_fem_kdtree_load_matcher():
    matcher = FEMLoadMatcher(search_tolerance_mm=2.0)
    
    cad_holes = [
        {"id": 1, "name": "Hole_01", "center": [10.0, 20.0, 0.0], "diameter": 6.35},
        {"id": 2, "name": "Hole_02", "center": [50.0, 20.0, 0.0], "diameter": 8.00}
    ]
    
    csv_text = """Hole_ID,X,Y,Z,Fx,Fy,Fz
1,10.5,20.1,0.0,2500,0,0
2,50.0,19.8,0.0,0,3200,0
3,99.0,99.0,0.0,500,500,0
"""
    loads = matcher.parse_csv_loads(csv_text)
    assert len(loads) == 3
    
    matched = matcher.match_loads_with_cad_holes(cad_holes, loads, tolerance_mm=2.0)
    assert matched["summary"]["matched_count"] == 2
    assert len(matched["orphan_loads"]) == 1
    assert matched["orphan_loads"][0]["load_id"] == "3"
    print(f"✅ FEM KDTree Spatial Load Matcher Passed: {matched['summary']['matched_count']} matched, {len(matched['orphan_loads'])} orphan.")

def test_adaptive_meshing():
    from app.core.mesh_engine import MeshEngine, GeometryConfig
    engine = MeshEngine()
    # Deliklerin kenara aşırı yakın olduğu bir konfigürasyon
    cfg = GeometryConfig(
        width=100.0, height=50.0,
        holes=[{"x": 6.0, "y": 25.0, "diameter": 8.0}], # d_left = 6.0 - 4.0 = 2.0 mm < 6.0 mm global mesh
        mesh_size_global=6.0,
        mesh_size_hole=1.2
    )
    adapted_cfg, info = engine._apply_adaptive_meshing(cfg)
    assert info["applied"] is True
    assert info["adapted_mesh_size_global"] < 6.0
    print(f"✅ Auto-Adaptive Meshing Passed: {info['adapted_mesh_size_global']} mm global mesh adapted for {info['min_geometric_distance']} mm min distance.")

if __name__ == "__main__":
    test_cad_engine_mesh_and_holes()
    test_curvature_profiler_and_dcm()
    test_fem_kdtree_load_matcher()
    test_adaptive_meshing()
    print("🎉 All AeroJoint V4.0 Enterprise Backend Tests Passed Successfully!")
