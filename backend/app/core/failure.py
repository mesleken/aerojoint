"""
Havacılık Hasar/Kırılma Kriterleri Motoru.

Birincil: Hashin (1980) — 4 bağımsız hasar modu
İkincil: Tsai-Wu — Genel eliptik etkileşim katsayısı
"""
import numpy as np
from dataclasses import dataclass
from .clt import OrthotropicMaterial

@dataclass
class FailureResult:
    """Tek bir katmandaki kırılma analizi sonucu."""
    ply_id: int
    angle: float
    
    # Hashin (BİRİNCİL)
    hashin_fiber_tension: float = 0.0
    hashin_fiber_compression: float = 0.0
    hashin_matrix_tension: float = 0.0
    hashin_matrix_compression: float = 0.0
    hashin_max_fi: float = 0.0
    hashin_failure_mode: str = "None"
    
    # Tsai-Wu (İKİNCİL)
    tsai_wu_fi: float = 0.0
    
    # Güvenlik Marjı — Hashin üzerinden hesaplanır (birincil)
    mos_hashin: float = float('inf')
    mos_tsai_wu: float = float('inf')
    min_mos: float = float('inf')
    governing_criterion: str = "Hashin"
    
    # Durum
    is_failed: bool = False


class FailureCriteriaEngine:
    """Katman katman Hashin ve Tsai-Wu analizi yapar."""
    
    @staticmethod
    def hashin_criteria(sigma_1: float, sigma_2: float, tau_12: float,
                        material: OrthotropicMaterial) -> dict:
        """
        Hashin Kırılma Kriterleri (1980).
        """
        Xt, Xc = material.Xt, material.Xc
        Yt, Yc = material.Yt, material.Yc
        S12 = material.S12
        
        fi_ft = (sigma_1 / Xt)**2 + (tau_12 / S12)**2 if sigma_1 > 0 else 0.0
        fi_fc = (sigma_1 / Xc)**2 if sigma_1 < 0 else 0.0
        fi_mt = (sigma_2 / Yt)**2 + (tau_12 / S12)**2 if sigma_2 > 0 else 0.0
        
        fi_mc = 0.0
        if sigma_2 < 0:
            if material.S23 is not None:
                S23 = material.S23
                fi_mc = ((sigma_2 / (2 * S23))**2 + 
                         ((Yc / (2 * S23))**2 - 1) * (sigma_2 / Yc) + 
                         (tau_12 / S12)**2)
            else:
                fi_mc = (sigma_2 / Yc)**2 + (tau_12 / S12)**2
        
        modes = {
            'Fiber Tension': fi_ft,
            'Fiber Compression': fi_fc,
            'Matrix Tension': fi_mt,
            'Matrix Compression': fi_mc
        }
        
        max_fi = max(modes.values())
        dominant_mode = max(modes, key=modes.get) if max_fi > 0 else "None"
        
        return {
            'fiber_tension': fi_ft,
            'fiber_compression': fi_fc,
            'matrix_tension': fi_mt,
            'matrix_compression': fi_mc,
            'max_fi': max_fi,
            'dominant_mode': dominant_mode
        }
    
    @staticmethod
    def tsai_wu_criterion(sigma_1: float, sigma_2: float, tau_12: float,
                           material: OrthotropicMaterial) -> dict:
        """
        Tsai-Wu Etkileşim Kırılma Kriteri (İKİNCİL).
        """
        Xt, Xc = material.Xt, material.Xc
        Yt, Yc = material.Yt, material.Yc
        S12 = material.S12
        
        F1 = 1.0/Xt - 1.0/Xc
        F2 = 1.0/Yt - 1.0/Yc
        F11 = 1.0 / (Xt * Xc)
        F22 = 1.0 / (Yt * Yc)
        F66 = 1.0 / (S12**2)
        F12 = -0.5 * np.sqrt(F11 * F22)
        
        a = (F11 * sigma_1**2 + F22 * sigma_2**2 + F66 * tau_12**2 + 
             2 * F12 * sigma_1 * sigma_2)
        b = F1 * sigma_1 + F2 * sigma_2
        
        if abs(a) < 1e-15:
            R = 1.0 / b if abs(b) > 1e-15 else float('inf')
        else:
            discriminant = b**2 + 4 * a
            R = (-b + np.sqrt(max(0, discriminant))) / (2 * a) if discriminant >= 0 else float('inf')
        
        fi = 1.0 / R if R > 0 else float('inf')
        
        return {'fi': fi, 'strength_ratio': R}
    
    @staticmethod
    def compute_margin_of_safety(failure_index: float) -> float:
        """
        Güvenlik Marjı: MoS = (1/FI) - 1
        """
        if failure_index <= 0:
            return float('inf')
        return (1.0 / failure_index) - 1.0
    
    def evaluate_ply(self, sigma_1: float, sigma_2: float, tau_12: float,
                     material: OrthotropicMaterial, ply_id: int, 
                     angle: float) -> FailureResult:
        """Tek bir katmanı Hashin (birincil) + Tsai-Wu (ikincil) ile değerlendir."""
        hashin = self.hashin_criteria(sigma_1, sigma_2, tau_12, material)
        tsai_wu = self.tsai_wu_criterion(sigma_1, sigma_2, tau_12, material)
        
        mos_h = self.compute_margin_of_safety(hashin['max_fi'])
        mos_tw = self.compute_margin_of_safety(tsai_wu['fi'])
        
        min_mos = mos_h
        governing = "Hashin"
        
        if mos_tw < mos_h:
            governing = "Hashin (Tsai-Wu daha kritik: MoS={:.3f})".format(mos_tw)
        
        return FailureResult(
            ply_id=ply_id,
            angle=angle,
            hashin_fiber_tension=hashin['fiber_tension'],
            hashin_fiber_compression=hashin['fiber_compression'],
            hashin_matrix_tension=hashin['matrix_tension'],
            hashin_matrix_compression=hashin['matrix_compression'],
            hashin_max_fi=hashin['max_fi'],
            hashin_failure_mode=hashin['dominant_mode'],
            tsai_wu_fi=tsai_wu['fi'],
            mos_hashin=mos_h,
            mos_tsai_wu=mos_tw,
            min_mos=min_mos,
            governing_criterion=governing,
            is_failed=(min_mos < 0)
        )
