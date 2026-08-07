import asyncio
from app.models.analysis import AnalysisRequest, HoleInput, PlyInput
from app.services.analysis_service import AnalysisService
from app.core.materials_db import MaterialsDB

def main():
    print("--- TESTING THEME 1: CUSTOM MATERIAL MANAGER ---")
    db = MaterialsDB()
    test_mat_id = "CUSTOM_TEST_CARBON"
    try:
        db.delete_material(test_mat_id)
    except ValueError:
        pass

    db.add_material(test_mat_id, {
        "name": "Custom Test Carbon Prepreg",
        "category": "Carbon/Epoxy",
        "source": "User Test",
        "ply_thickness": 0.125,
        "elastic": {"E1": 140000, "E2": 10000, "G12": 5500, "nu12": 0.3},
        "strength": {"Xt": 1600, "Xc": 1300, "Yt": 60, "Yc": 220, "S12": 80}
    })
    print("Custom Material Added Successfully.")
    
    mat = db.get_material(test_mat_id)
    assert mat.E1 == 140000
    print("Custom Material Retrieved Successfully.")

    print("\n--- TESTING THEME 2 & 3: PDM, PUCK & CLAMP-UP TORQUE ---")
    plies = [
        PlyInput(material_id=test_mat_id, angle=0.0, thickness=0.125),
        PlyInput(material_id=test_mat_id, angle=45.0, thickness=0.125),
        PlyInput(material_id=test_mat_id, angle=-45.0, thickness=0.125),
        PlyInput(material_id=test_mat_id, angle=90.0, thickness=0.125),
    ]

    req = AnalysisRequest(
        width=100.0,
        height=50.0,
        holes=[HoleInput(x=30.0, y=25.0, diameter=6.35, load_magnitude=2000.0, load_angle=0.0, torque=15.0)],
        plies=plies,
        constraint_type="fixed",
        mesh_size_global=5.0,
        mesh_size_hole=1.0,
        enable_pdm=True,
        failure_criterion="Puck"
    )

    service = AnalysisService()
    result = service.run_full_analysis(req.model_dump())

    print(f"Layup: {result['layup_notation']}")
    print(f"Overall Status: {result['overall_status']}")
    print(f"Governing Criterion: {result['governing_criterion']}")
    print(f"Min MoS: {result['min_mos']:.3f}")
    if 'pdm_results' in result:
        pdm = result['pdm_results']
        print(f"PDM FPF Load: {pdm['first_ply_failure_load_N']:.0f} N")
        print(f"PDM Ultimate Load: {pdm['ultimate_load_N']:.0f} N")
        print(f"Stress Frames Count: {len(result['stress_frames'])}")

    print("\n--- CLEANING UP TEST MATERIAL ---")
    db.delete_material(test_mat_id)
    print("Cleanup Complete. ALL V2 THEMES TESTED CLEANLY!")

if __name__ == '__main__':
    main()
