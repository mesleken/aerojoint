"""
Pydantic Analiz İstek ve Yanıt Şablonları (Models) - Pydantic v2 Uyumlu
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PlyInput(BaseModel):
    material_id: str = "T300_5208"
    angle: float = 0.0
    thickness: float = 0.125

class HoleInput(BaseModel):
    x: float = 50.0
    y: float = 25.0
    diameter: float = 6.35
    load_magnitude: float = 5000.0
    load_angle: float = 0.0
    torque: float = 0.0  # Cıvata Sıkma Torku (Nm)

class LoadCase(BaseModel):
    name: str = "Case 1"
    load_magnitude: float = 5000.0
    load_angle: float = 0.0

class AnalysisRequest(BaseModel):
    width: float = 200.0
    height: float = 100.0
    plies: List[PlyInput] = []
    holes: List[HoleInput] = []
    constraint_type: str = "fixed"
    mesh_size_global: float = 5.0
    mesh_size_hole: float = 1.0
    enable_pdm: bool = False
    failure_criterion: str = "Hashin"  # Hashin, Tsai-Wu, Puck
    load_cases: Optional[List[LoadCase]] = None

class PlyResultResponse(BaseModel):
    ply_id: int
    angle: float
    hashin_max_fi: float
    dominant_mode: str
    tsai_wu_fi: float
    mos_hashin: float
    is_failed: bool

class AnalysisResponse(BaseModel):
    layup_notation: str
    total_thickness: float
    min_mos: float
    overall_status: str
    governing_criterion: str
    critical_ply: int
    critical_angle: float
    critical_mode: str
    ply_results: List[PlyResultResponse]
    A_matrix: List[List[float]]
    B_matrix: List[List[float]]
    D_matrix: List[List[float]]
    B_nonzero: bool
    applied_load: float
    computation_time_ms: float
    mesh_summary: Dict[str, Any]
    nodes: List[List[float]]
    elements: List[List[int]]
    nodal_stresses: List[List[float]]
