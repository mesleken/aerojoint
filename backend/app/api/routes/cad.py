"""
AeroJoint V3.0 CAD & FEM Yük Entegrasyonu API Rotaları.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from ...core.cad_engine import CADEngine
from ...core.fem_load_matcher import FEMLoadMatcher

router = APIRouter(prefix="/api/cad", tags=["CAD & 3D Integration"])

cad_engine = CADEngine()
load_matcher = FEMLoadMatcher()


class CurvatureProfileRequest(BaseModel):
    gaussian_curvature: Optional[float] = 0.0
    hole_diameter: Optional[float] = 6.35
    radius_of_curvature: Optional[float] = 1000.0


class ForceTransformRequest(BaseModel):
    normal_vector: List[float] = Field(default=[0.0, 0.0, 1.0], min_length=3, max_length=3)
    force_global: List[float] = Field(default=[1000.0, 0.0, 0.0], min_length=3, max_length=3)
    shear_angle_deg: Optional[float] = 0.0


@router.post("/upload-step")
async def upload_cad_file(file: UploadFile = File(...)):
    """
    3B CAD dosyasını (STEP, STL, OBJ) alır, parçayı ayrıştırır, 
    otomatik delikleri ve eğrilik istatistiklerini döner.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Boş dosya yüklendi.")

    res = cad_engine.load_cad_file(content, file.filename)
    return res


@router.post("/match-loads")
async def match_loads(
    tolerance_mm: float = Form(2.0),
    cad_holes_json: str = Form(...),
    file: UploadFile = File(...)
):
    """
    CSV yük dosyası ile CAD deliklerini uzaysal KDTree kullanarak eşleştirir.
    """
    import json
    try:
        cad_holes = json.loads(cad_holes_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geçersiz CAD delik JSON verisi: {str(e)}")

    csv_text = (await file.read()).decode("utf-8")
    fem_loads = load_matcher.parse_csv_loads(csv_text)

    match_result = load_matcher.match_loads_with_cad_holes(
        cad_holes=cad_holes,
        fem_loads=fem_loads,
        tolerance_mm=tolerance_mm
    )

    return match_result


@router.post("/curvature-profile")
async def get_curvature_profile(req: CurvatureProfileRequest):
    """
    Tıklanan yüzey için Gauss eğriliği ve Akıllı Karar Ağacı analiz önerisini döner.
    """
    g_curv = req.gaussian_curvature or 0.0
    if abs(g_curv) < 1e-3:
        recommended = "Option_1_Tangent_Plane"
        method_title = "Teğet Düzlem İndirgemesi (Tangent Plane)"
        explanation = "Yüzey düzleme yakındır. 2B düzlem stress transformasyonu en hızlı ve hassas sonucu verir."
    elif abs(g_curv) < 1e-1:
        recommended = "Option_2_Geodesic"
        method_title = "Jeodezik Eğri Yayılımı (Geodesic Curve)"
        explanation = "Tek yönlü eğri (silindir). Delikler arası mesafeler 3B jeodezik yay uzunluklarıyla hesaplanır."
    else:
        recommended = "Option_3_Kinematic_Draping"
        method_title = "Kinematik Serim (Kinematic Draping)"
        explanation = "Çift eğrili (küresel) yapı. Kompozit elyaf serim kayması ve stiffness rotasyonu uygulanacak."

    return {
        "gaussian_curvature": g_curv,
        "recommended_option": recommended,
        "method_title": method_title,
        "explanation": explanation
    }


@router.post("/transform-forces")
async def transform_forces(req: ForceTransformRequest):
    """
    3B Global kuvvet vektörünü Yonlü Kosinüs Matrisi (DCM) ile 2B Lokal Düzlem Yüklerine dönüştürür.
    """
    R = cad_engine.compute_direction_cosine_matrix(tuple(req.normal_vector))
    transformed = cad_engine.transform_3d_force_to_2d_plane(req.force_global, R)

    return {
        "DCM_Matrix": R.tolist(),
        "transformed_force": transformed
    }
