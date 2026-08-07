"""
FastAPI Malzeme Kütüphanesi Endpoint'leri
"""
from fastapi import APIRouter, HTTPException
from ...core.materials_db import MaterialsDB

router = APIRouter(prefix="/api/materials", tags=["Materials"])

@router.get("/")
async def list_materials():
    """Tüm malzemelerin listesini getir."""
    db = MaterialsDB()
    return {"materials": db.list_materials()}

@router.get("/{material_id}")
async def get_material(material_id: str):
    """Belirli bir malzemenin detaylı özelliklerini getir."""
    db = MaterialsDB()
    try:
        mat = db.get_material(material_id)
        return {"material": mat.__dict__}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/")
async def add_custom_material(material_id: str, material_data: dict):
    """
    Yeni özel malzeme tanımı ekle.
    Mühendislerin özel prepreg verilerini yüklemesine olanak tanır.
    """
    db = MaterialsDB()
    try:
        db.add_material(material_id, material_data)
        return {"status": "added", "material_id": material_id}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
