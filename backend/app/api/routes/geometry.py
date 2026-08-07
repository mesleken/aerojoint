"""
FastAPI Geometri ve Ön İzleme Endpoint'leri
"""
from fastapi import APIRouter, HTTPException
from ...core.mesh_engine import MeshEngine, GeometryConfig, HAS_GMSH

router = APIRouter(prefix="/api/geometry", tags=["Geometry"])

@router.post("/mesh")
async def generate_mesh_preview(config_data: dict):
    """Sadece mesh/geometri ön izlemesi üret."""
    if not HAS_GMSH:
        return {"status": "fallback", "message": "Gmsh yüklü değil, varsayılan grid gösterilecek."}
    
    try:
        cfg = GeometryConfig(
            width=float(config_data.get('width', 200)),
            height=float(config_data.get('height', 100)),
            holes=config_data.get('holes', []),
            mesh_size_global=float(config_data.get('mesh_size_global', 5.0)),
            mesh_size_hole=float(config_data.get('mesh_size_hole', 1.0))
        )
        engine = MeshEngine()
        mesh_result = engine.create_mesh(cfg)
        return {
            "status": "success",
            "nodes": mesh_result['nodes'].tolist(),
            "elements": mesh_result['elements'].tolist(),
            "statistics": mesh_result['statistics']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
