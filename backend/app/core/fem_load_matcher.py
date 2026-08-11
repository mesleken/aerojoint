"""
AeroJoint V3.0 FEM Yük ve Geometri Eşleştirme Motoru (FEM Load Matcher).

Bu modül:
1. Nastran / Abaqus / Ansys veya CSV kaynaklı FEM yük listelerini ayrıştırır.
2. scipy.spatial.cKDTree kullanarak O(log N) hızında 3B uzaysal koordinat eşleştirmesi yapar.
3. Tolerans mekanizması (varsayılan 2.0 mm küresel arama yarıçapı) çalıştırır.
4. Eşleşmeyen yetim yükleri (orphan loads) ve yük atanmamış delikleri tespit edip raporlar.
"""

import io
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from typing import List, Dict, Any, Tuple

class FEMLoadMatcher:
    """Uzaysal KDTree FEM Yük ve CAD Delik Eşleştirici."""

    def __init__(self, search_tolerance_mm: float = 2.0):
        self.search_tolerance_mm = search_tolerance_mm

    def parse_csv_loads(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        CSV formatındaki yük verisini okur.
        Beklenen kolonlar: [Hole_ID, X, Y, Z, Fx, Fy, Fz] veya [ID, X, Y, Z, Load_X, Load_Y, Load_Z]
        """
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Kolon isimlerini standartlaştır
        cols = [c.strip().lower() for c in df.columns]
        df.columns = cols

        records = []
        for idx, row in df.iterrows():
            # Kolon isim eşleme
            raw_id = row.get('hole_id', row.get('id', row.get('node', idx + 1)))
            try:
                hole_id = str(int(raw_id))
            except Exception:
                hole_id = str(raw_id).strip()
            x = float(row.get('x', 0.0))
            y = float(row.get('y', 0.0))
            z = float(row.get('z', 0.0))
            fx = float(row.get('fx', row.get('load_x', 0.0)))
            fy = float(row.get('fy', row.get('load_y', 0.0)))
            fz = float(row.get('fz', row.get('load_z', 0.0)))
            
            mag = float(np.hypot(fx, fy))

            records.append({
                "load_id": hole_id,
                "coord": [x, y, z],
                "force": [fx, fy, fz],
                "magnitude_in_plane": mag
            })

        return records

    def match_loads_with_cad_holes(
        self, 
        cad_holes: List[Dict[str, Any]], 
        fem_loads: List[Dict[str, Any]],
        tolerance_mm: float = 2.0
    ) -> Dict[str, Any]:
        """
        CAD delik merkezleri (X,Y,Z) ile FEM yük koordinatlarını cKDTree ile eşleştirir.
        """
        if not cad_holes:
            return {
                "matched_results": [],
                "orphan_loads": fem_loads,
                "unmatched_holes": [],
                "summary": {
                    "total_holes": 0,
                    "total_loads": len(fem_loads),
                    "matched_count": 0,
                    "status": "NO_CAD_HOLES"
                }
            }

        # CAD delik koordinatlarını KDTree ağacına diz
        cad_coords = np.array([h["center"] for h in cad_holes])
        tree = cKDTree(cad_coords)

        matched_results = []
        matched_hole_indices = set()
        orphan_loads = []

        for load_item in fem_loads:
            load_coord = np.array(load_item["coord"])
            
            # Ağaçta en yakın CAD deliğini ara
            distance, nearest_idx = tree.query(load_coord, distance_upper_bound=tolerance_mm)

            if distance <= tolerance_mm and nearest_idx < len(cad_holes):
                cad_hole = cad_holes[nearest_idx]
                matched_hole_indices.add(nearest_idx)

                matched_results.append({
                    "hole_id": cad_hole["id"],
                    "hole_name": cad_hole.get("name", f"Hole_{cad_hole['id']}"),
                    "cad_center": cad_hole["center"],
                    "load_center": load_item["coord"],
                    "diameter": cad_hole["diameter"],
                    "distance_error_mm": float(distance),
                    "force_vector": load_item["force"],
                    "magnitude": load_item["magnitude_in_plane"],
                    "match_status": "EXACT" if distance < 1e-3 else "TOLERANCE_MATCH"
                })
            else:
                orphan_loads.append(load_item)

        # Yük atanmamış boşta kalan delikler
        unmatched_holes = [
            cad_holes[i] for i in range(len(cad_holes)) if i not in matched_hole_indices
        ]

        status = "ALL_MATCHED" if len(orphan_loads) == 0 and len(unmatched_holes) == 0 else "WARNING_PARTIAL_MATCH"

        return {
            "matched_results": matched_results,
            "orphan_loads": orphan_loads,
            "unmatched_holes": unmatched_holes,
            "summary": {
                "total_holes": len(cad_holes),
                "total_loads": len(fem_loads),
                "matched_count": len(matched_results),
                "orphan_count": len(orphan_loads),
                "unassigned_holes_count": len(unmatched_holes),
                "tolerance_used_mm": tolerance_mm,
                "status": status
            }
        }
