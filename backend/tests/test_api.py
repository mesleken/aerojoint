"""
API Integration Unit Tests
"""
import pytest
from app.services.analysis_service import AnalysisService

def test_analysis_service_end_to_end():
    service = AnalysisService()
    request_data = {
        "width": 100.0,
        "height": 50.0,
        "plies": [
            {"material_id": "T300_5208", "angle": 0.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 45.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": -45.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 90.0, "thickness": 0.125}
        ],
        "holes": [
            {"x": 50.0, "y": 25.0, "diameter": 6.0, "load_magnitude": 2000.0, "load_angle": 0.0}
        ],
        "constraint_type": "fixed",
        "mesh_size_global": 10.0,
        "mesh_size_hole": 2.0
    }
    
    result = service.run_full_analysis(request_data)
    
    assert 'layup_notation' in result
    assert result['total_thickness'] == 0.5
    assert len(result['ply_results']) == 4
    assert 'min_mos' in result
    assert result['overall_status'] in ['PASS', 'FAIL']
    assert len(result['A_matrix']) == 3
    assert len(result['nodes']) > 0
    assert len(result['elements']) > 0
