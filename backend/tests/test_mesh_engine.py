"""
Mesh Engine Unit Tests
"""
import pytest
from app.core.mesh_engine import GeometryConfig, MeshEngine, HAS_GMSH

def test_geometry_config_dataclass():
    config = GeometryConfig(
        width=100.0,
        height=50.0,
        holes=[{'x': 50.0, 'y': 25.0, 'diameter': 6.0}],
        mesh_size_global=4.0,
        mesh_size_hole=0.8
    )
    assert config.width == 100.0
    assert config.height == 50.0
    assert len(config.holes) == 1
    assert config.holes[0]['diameter'] == 6.0

@pytest.mark.skipif(not HAS_GMSH, reason="Gmsh is not installed")
def test_mesh_engine_generation():
    engine = MeshEngine()
    config = GeometryConfig(
        width=40.0,
        height=20.0,
        holes=[{'x': 20.0, 'y': 10.0, 'diameter': 4.0}],
        mesh_size_global=3.0,
        mesh_size_hole=0.8,
        boundary_layers=2
    )
    mesh_data = engine.create_mesh(config)
    assert 'nodes' in mesh_data
    assert 'elements' in mesh_data
    assert len(mesh_data['nodes']) > 0
    assert len(mesh_data['elements']) > 0
    assert mesh_data['statistics']['n_nodes'] == len(mesh_data['nodes'])
