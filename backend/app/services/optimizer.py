import copy
from typing import List, Dict, Any
from .analysis_service import AnalysisService

class LayupOptimizer:
    """
    Otonom Laminat Optimizasyon Motoru (Heuristic Search).
    Belirli bir yük durumunda MoS > 0 şartını sağlayan en hafif 
    (en ince) standart havacılık dizilimini bulur.
    """
    
    STANDARD_LAYUPS = [
        # (Ad, Açılar, Simetrik mi)
        ("Tension/Compression (0 Dominated)", [0, 0, 45, -45, 90], True),
        ("Quasi-Isotropic (Standard)", [0, 45, -45, 90], True),
        ("Shear Dominated (45 Dominated)", [45, -45, 45, -45, 0, 90], True),
        ("Cross-Ply", [0, 90, 0, 90], True),
        ("Thin Quasi-Isotropic", [0, 45, -45, 90], False),
        ("Thin Shear", [45, -45], True)
    ]
    
    def __init__(self, material_id: str = "T300_5208", ply_thickness: float = 0.125):
        self.material_id = material_id
        self.ply_thickness = ply_thickness
        self.analysis_service = AnalysisService()
        
    def _build_plies(self, angles: List[float], symmetric: bool) -> List[Dict]:
        plies = []
        full_angles = angles + angles[::-1] if symmetric else angles
        for a in full_angles:
            plies.append({
                "material_id": self.material_id,
                "angle": a,
                "thickness": self.ply_thickness
            })
        return plies

    def optimize(self, base_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        base_request içinde geometri ve yükler sabit kalacak şekilde 
        en iyi katman dizilimini arar.
        """
        best_layup = None
        min_thickness = float('inf')
        best_mos = -1.0
        
        results_log = []
        
        for name, angles, is_sym in self.STANDARD_LAYUPS:
            test_request = copy.deepcopy(base_request)
            test_request['plies'] = self._build_plies(angles, is_sym)
            
            # Hizli calismasi icin PDM kapali analiz yapalim
            test_request['enable_pdm'] = False 
            
            try:
                res = self.analysis_service.run_full_analysis(test_request)
                mos = res.get('min_mos', -1.0)
                thickness = res.get('total_thickness', 999.0)
                
                status = "PASS" if mos >= 0.0 else "FAIL"
                results_log.append({
                    "name": name,
                    "thickness": thickness,
                    "mos": mos,
                    "status": status
                })
                
                if mos >= 0.0 and thickness < min_thickness:
                    min_thickness = thickness
                    best_layup = {
                        "name": name,
                        "plies": test_request['plies'],
                        "thickness": thickness,
                        "mos": mos
                    }
            except Exception as e:
                results_log.append({"name": name, "error": str(e)})
                
        return {
            "best_layup": best_layup,
            "all_results": results_log
        }
