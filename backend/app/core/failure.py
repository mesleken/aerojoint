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
    def puck_criterion(sigma_1: float, sigma_2: float, tau_12: float,
                       material: OrthotropicMaterial) -> dict:
        """
        Puck (2D) Kırılma Kriteri (Havacılık Gelişmiş Eki).
        """
        Xt, Xc = material.Xt, material.Xc
        Yt, Yc = material.Yt, material.Yc
        S12 = material.S12
        
        # Elyaf Kırılması (Fiber Failure - FF)
        f_FF = (sigma_1 / Xt) if sigma_1 > 0 else (abs(sigma_1) / Xc)
        
        # Elyaf Arası/Matris Kırılması (Inter-Fiber Failure - IFF)
        p_t = 0.35  # Eğim parametresi (parallely-transverse tension)
        p_c = 0.30  # Eğim parametresi (parallely-transverse compression)
        
        f_IFF = 0.0
        iff_mode = "None"
        
        if sigma_2 >= 0:
            # Mode A (Enine Çekme + Makaslama)
            term1 = (tau_12 / S12)**2
            term2 = (1.0 - p_t * (Yt / S12))**2 * (sigma_2 / Yt)**2
            f_IFF = np.sqrt(term1 + term2) + p_t * (sigma_2 / S12)
            iff_mode = "Puck Mode A (Matrix Tension)"
        else:
            # Mode B / Mode C (Enine Basma + Makaslama)
            R_A = S12 / (2.0 * p_c) if p_c > 0 else S12
            if abs(sigma_2) <= R_A:
                # Mode B
                f_IFF = (1.0 / S12) * (np.sqrt(tau_12**2 + (p_c * sigma_2)**2) + p_c * sigma_2)
                iff_mode = "Puck Mode B (Matrix Shear-Comp)"
            else:
                # Mode C
                f_IFF = ((tau_12 / (2.0 * (1.0 + p_c) * S12))**2 + (sigma_2 / Yc)**2) * (Yc / abs(sigma_2))
                iff_mode = "Puck Mode C (Matrix Compression)"
        
        max_fi = max(f_FF**2, f_IFF**2)
        dominant = "Puck FF (Fiber)" if f_FF**2 >= f_IFF**2 else iff_mode
        
        return {
            'fiber_fi': f_FF**2,
            'iff_fi': f_IFF**2,
            'max_fi': max_fi,
            'dominant_mode': dominant
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
    def compute_margin_of_safety(failure_index: float, is_quadratic: bool = False) -> float:
        """
        Güvenlik Marjı: 
        Doğrusal/R tabanlı FI için: MoS = (1/FI) - 1
        Kuadratik FI için (Hashin): MoS = (1/sqrt(FI)) - 1
        """
        if failure_index <= 0:
            return float('inf')
        
        if is_quadratic:
            return (1.0 / np.sqrt(failure_index)) - 1.0
        else:
            return (1.0 / failure_index) - 1.0
    
    def evaluate_ply(self, sigma_1: float, sigma_2: float, tau_12: float,
                     material: OrthotropicMaterial, ply_id: int, 
                     angle: float) -> FailureResult:
        """Tek bir katmanı Hashin (birincil) + Tsai-Wu (ikincil) ile değerlendir."""
        hashin = self.hashin_criteria(sigma_1, sigma_2, tau_12, material)
        tsai_wu = self.tsai_wu_criterion(sigma_1, sigma_2, tau_12, material)
        
        # Hashin hasar indeksleri kuadratiktir (stress karesiyle orantılıdır), 
        # bu nedenle mukavemet oranı (Strength Ratio, R) = 1 / sqrt(FI)
        mos_h = self.compute_margin_of_safety(hashin['max_fi'], is_quadratic=True)
        # Tsai-Wu fi değeri halihazırda (1/R) olarak hesaplandığı için doğrusaldır
        mos_tw = self.compute_margin_of_safety(tsai_wu['fi'], is_quadratic=False)
        
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
