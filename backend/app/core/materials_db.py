"""
Harici JSON Malzeme Kütüphanesi Yöneticisi.

Neden JSON? TUSAŞ/Baykar mühendisleri kendi gizli prepreg malzemelerini
(özel reçineli karbon fiber) kodla uğraşmadan kütüphaneye ekleyebilsin.
"""
import json
import os
from pathlib import Path
from typing import Optional
from .clt import OrthotropicMaterial

# Varsayılan malzeme dosyası yolu
DEFAULT_MATERIALS_PATH = Path(__file__).parent.parent.parent / "data" / "materials.json"


class MaterialsDB:
    """JSON tabanlı malzeme kütüphanesi."""
    
    def __init__(self, json_path: Optional[str] = None):
        self.json_path = Path(json_path) if json_path else DEFAULT_MATERIALS_PATH
        self._materials = {}
        self._load()
    
    def _load(self):
        """JSON dosyasını yükle."""
        if not self.json_path.exists():
            raise FileNotFoundError(
                f"Malzeme kütüphanesi bulunamadı: {self.json_path}"
            )
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._materials = data.get('materials', {})
    
    def list_materials(self) -> list[dict]:
        """Tüm malzemelerin listesini döndür."""
        return [
            {
                'id': mat_id,
                'name': mat_data['name'],
                'category': mat_data.get('category', 'Unknown'),
                'source': mat_data.get('source', ''),
                'ply_thickness': mat_data.get('ply_thickness', 0.125)
            }
            for mat_id, mat_data in self._materials.items()
        ]
    
    def get_material(self, material_id: str) -> OrthotropicMaterial:
        """Belirtilen ID ile malzemeyi OrthotropicMaterial nesnesine dönüştür."""
        if material_id not in self._materials:
            available = ', '.join(self._materials.keys())
            raise ValueError(
                f"Malzeme '{material_id}' bulunamadı. "
                f"Mevcut malzemeler: {available}"
            )
        
        mat = self._materials[material_id]
        elastic = mat['elastic']
        strength = mat['strength']
        
        return OrthotropicMaterial(
            name=mat['name'],
            E1=elastic['E1'],
            E2=elastic['E2'],
            G12=elastic['G12'],
            nu12=elastic['nu12'],
            Xt=strength['Xt'],
            Xc=strength['Xc'],
            Yt=strength['Yt'],
            Yc=strength['Yc'],
            S12=strength['S12'],
            S23=strength.get('S23')
        )
    
    def add_material(self, material_id: str, material_data: dict) -> bool:
        """
        Yeni bir malzeme ekle ve JSON dosyasını güncelle.
        
        Bu yöntem sayesinde mühendisler kendi özel prepreg malzemelerini
        yazılımı yeniden derlemeden ekleyebilir.
        """
        if material_id in self._materials:
            raise ValueError(f"'{material_id}' zaten mevcut. Güncellemek için update_material kullanın.")
        
        # Gerekli alanları doğrula
        required_elastic = ['E1', 'E2', 'G12', 'nu12']
        required_strength = ['Xt', 'Xc', 'Yt', 'Yc', 'S12']
        
        elastic = material_data.get('elastic', {})
        strength = material_data.get('strength', {})
        
        for field in required_elastic:
            if field not in elastic:
                raise ValueError(f"Eksik elastik özellik: {field}")
        
        for field in required_strength:
            if field not in strength:
                raise ValueError(f"Eksik mukavemet özelliği: {field}")
        
        # Termodinamik tutarlılık kontrolü
        nu21 = elastic['nu12'] * elastic['E2'] / elastic['E1']
        if elastic['nu12'] * nu21 >= 1.0:
            raise ValueError("Termodinamik tutarsızlık: ν12·ν21 ≥ 1")
        
        self._materials[material_id] = material_data
        self._save()
        return True
    
    def delete_material(self, material_id: str) -> bool:
        """Belirtilen ID'li özel malzemeyi kütüphaneden sil."""
        if material_id not in self._materials:
            raise ValueError(f"Malzeme '{material_id}' bulunamadı.")
        
        del self._materials[material_id]
        self._save()
        return True

    def _save(self):
        """Güncel malzeme verisini JSON dosyasına yaz."""
        data = {
            'version': '1.0',
            'description': 'AeroJoint Havacılık Kompozit Malzeme Kütüphanesi',
            'materials': self._materials
        }
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
