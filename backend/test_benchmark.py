import asyncio
from app.models.analysis import AnalysisRequest, HoleInput, PlyInput
from app.services.analysis_service import AnalysisService
import json

def main():
    # Benchmark 16-ply Quasi-Isotropic Laminate [0/45/-45/90]2s
    # Total thickness = 16 * 0.125 = 2.0 mm
    # Hole diameter = 6.35 mm
    plies = [
        PlyInput(material_id="T300_5208", angle=0.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=-45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=90.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=0.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=-45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=90.0, thickness=0.125),
        # Symmetric part
        PlyInput(material_id="T300_5208", angle=90.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=-45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=0.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=90.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=-45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=45.0, thickness=0.125),
        PlyInput(material_id="T300_5208", angle=0.0, thickness=0.125),
    ]
    
    # 36 mm width (W/D ~ 6) to avoid net tension failure
    # 70 mm height (e/D ~ 6) to avoid shear-out failure
    # P = 5000 N -> Bearing stress = P / (D * t) = 5000 / (6.35 * 2.0) = 393.7 MPa
    # Typical pin-bearing strength for T300/5208 is ~400-450 MPa
    
    req = AnalysisRequest(
        width=70.0,
        height=36.0,
        holes=[HoleInput(x=35.0, y=18.0, diameter=6.35, load_magnitude=5000.0, load_angle=0.0)],
        plies=plies,
        constraint_type="fixed",
        mesh_size_global=3.0,
        mesh_size_hole=0.5
    )
    
    service = AnalysisService()
    result = service.run_full_analysis(req.model_dump())
    
    for ply in result['ply_results']:
        print(f"Ply {ply['ply_id']} ({ply['angle']} deg) - Hashin FI: {ply['hashin_max_fi']:.2f}, Tsai-Wu FI: {ply['tsai_wu_fi']:.2f}, MoS: {ply['mos_hashin']:.3f}, Failed: {ply['is_failed']}")

    import math
    max_vm = max([math.sqrt(max(0, s[0]**2 - s[0]*s[1] + s[1]**2 + 3*s[2]**2)) for s in result['nodal_stresses']])
    print(f"\n==============================")
    print(f"Max Von Mises Stress in Laminate: {max_vm:.1f} MPa")
    print(f"Nominal Bearing Stress (P/Dt): {5000/(6.35*2.0):.1f} MPa")
    print(f"==============================")

if __name__ == '__main__':
    main()
