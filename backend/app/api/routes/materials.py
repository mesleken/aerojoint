from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from ...core.materials_db import MaterialsDB

router = APIRouter(prefix="/api/materials", tags=["Materials"])

class ElasticProperties(BaseModel):
    E1: float = Field(..., gt=0, description="11 yönü elastisite modülü (MPa)")
    E2: float = Field(..., gt=0, description="22 yönü elastisite modülü (MPa)")
    G12: float = Field(..., gt=0, description="Kayma modülü (MPa)")
    nu12: float = Field(..., gt=0, lt=0.5, description="Poisson oranı")

class StrengthProperties(BaseModel):
    Xt: float = Field(..., gt=0, description="Boyuna çekme mukavemeti (MPa)")
    Xc: float = Field(..., gt=0, description="Boyuna basma mukavemeti (MPa)")
    Yt: float = Field(..., gt=0, description="Enine çekme mukavemeti (MPa)")
    Yc: float = Field(..., gt=0, description="Enine basma mukavemeti (MPa)")
    S12: float = Field(..., gt=0, description="Kayma mukavemeti (MPa)")
    S23: Optional[float] = Field(None, description="Enine kayma mukavemeti (MPa)")

class CustomMaterialCreate(BaseModel):
    id: str = Field(..., min_length=2, description="Benzersiz malzeme kimliği")
    name: str = Field(..., min_length=2, description="Malzeme adı")
    category: Optional[str] = "Custom"
    source: Optional[str] = "User Defined"
    ply_thickness: float = Field(0.125, gt=0, description="Varsayılan katman kalınlığı (mm)")
    elastic: ElasticProperties
    strength: StrengthProperties

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
async def add_custom_material(mat_input: CustomMaterialCreate):
    """
    Yeni özel malzeme tanımı ekle.
    Mühendislerin özel prepreg verilerini yüklemesine olanak tanır.
    """
    db = MaterialsDB()
    try:
        material_data = mat_input.model_dump()
        material_id = material_data.pop('id')
        db.add_material(material_id, material_data)
        return {"status": "added", "material_id": material_id}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.delete("/{material_id}")
async def delete_material(material_id: str):
    """Özel bir malzemeyi kütüphaneden sil."""
    db = MaterialsDB()
    try:
        db.delete_material(material_id)
        return {"status": "deleted", "material_id": material_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
