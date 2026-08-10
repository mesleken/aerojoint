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
    
    # Güvenlik Marjı — (Load Factor - 1)
    mos_hashin: float = float('inf')
    mos_tsai_wu: float = float('inf')
    min_mos: float = float('inf')
    governing_criterion: str = "Hashin"
    
    # Durum
    is_failed: bool = False


class FailureCriteriaEngine:
    """Katman katman Hashin ve Tsai-Wu analizi yapar (Termal+Mekanik birleşik)."""
    
    @staticmethod
    def _solve_lambda(A: float, B: float, C: float) -> list:
        """
        A*lambda^2 + B*lambda + (C - 1) = 0 denklemini çözer.
        Pozitif köklerin listesini döndürür.
        """
        C_prime = C - 1.0
        
        # A -> 0 dejenere durumu (Sadece termal ofset var veya ilgili mekanik yük 0)
        if abs(A) < 1e-15:
            if abs(B) < 1e-15:
                return []
            lam = -C_prime / B
            return [lam] if lam > 0 else []
            
        discriminant = B**2 - 4*A*C_prime
        if discriminant < 0:
            return []
            
        r1 = (-B + np.sqrt(discriminant)) / (2*A)
        r2 = (-B - np.sqrt(discriminant)) / (2*A)
        
        return sorted([r for r in (r1, r2) if r > 0])

    @staticmethod
    def hashin_criteria(sm: list, st: list, material: OrthotropicMaterial) -> dict:
        """
        Hashin Kırılma Kriterleri (1980).
        sm: Mekanik stres [sigma_1, sigma_2, tau_12]
        st: Termal stres [sigma_1, sigma_2, tau_12]
        """
        Xt, Xc = material.Xt, material.Xc
        Yt, Yc = material.Yt, material.Yc
        S12 = material.S12
        S23 = material.S23 if material.S23 is not None else Yc / 2.0
        
        # Fiber Tension: Condition (sigma_1(lam) >= 0)
        A_ft = (sm[0]/Xt)**2 + (sm[2]/S12)**2
        B_ft = 2*(sm[0]*st[0])/(Xt**2) + 2*(sm[2]*st[2])/(S12**2)
        C_ft = (st[0]/Xt)**2 + (st[2]/S12)**2
        
        fi_ft = A_ft + B_ft + C_ft if (sm[0] + st[0]) >= 0 else 0.0
        
        lam_ft = float('inf')
        for lam in FailureCriteriaEngine._solve_lambda(A_ft, B_ft, C_ft):
            if (st[0] + lam * sm[0]) >= 0:
                lam_ft = lam
                break

        # Fiber Compression: Condition (sigma_1(lam) < 0)
        A_fc = (sm[0]/Xc)**2
        B_fc = 2*(sm[0]*st[0])/(Xc**2)
        C_fc = (st[0]/Xc)**2
        
        fi_fc = A_fc + B_fc + C_fc if (sm[0] + st[0]) < 0 else 0.0
        
        lam_fc = float('inf')
        for lam in FailureCriteriaEngine._solve_lambda(A_fc, B_fc, C_fc):
            if (st[0] + lam * sm[0]) < 0:
                lam_fc = lam
                break

        # Matrix Tension: Condition (sigma_2(lam) >= 0)
        A_mt = (sm[1]/Yt)**2 + (sm[2]/S12)**2
        B_mt = 2*(sm[1]*st[1])/(Yt**2) + 2*(sm[2]*st[2])/(S12**2)
        C_mt = (st[1]/Yt)**2 + (st[2]/S12)**2
        
        fi_mt = A_mt + B_mt + C_mt if (sm[1] + st[1]) >= 0 else 0.0
        
        lam_mt = float('inf')
        for lam in FailureCriteriaEngine._solve_lambda(A_mt, B_mt, C_mt):
            if (st[1] + lam * sm[1]) >= 0:
                lam_mt = lam
                break

        # Matrix Compression: Condition (sigma_2(lam) < 0)
        A_mc = (sm[1]/(2*S23))**2 + ((Yc/(2*S23))**2 - 1)*(sm[1]/Yc) + (sm[2]/S12)**2
        B_mc = 2*(sm[1]*st[1])/((2*S23)**2) + ((Yc/(2*S23))**2 - 1)*(st[1]/Yc) + 2*(sm[2]*st[2])/(S12**2)
        C_mc = (st[1]/(2*S23))**2 + ((Yc/(2*S23))**2 - 1)*(st[1]/Yc) + (st[2]/S12)**2
        
        fi_mc = A_mc + B_mc + C_mc if (sm[1] + st[1]) < 0 else 0.0
        
        lam_mc = float('inf')
        for lam in FailureCriteriaEngine._solve_lambda(A_mc, B_mc, C_mc):
            if (st[1] + lam * sm[1]) < 0:
                lam_mc = lam
                break

        modes_fi = {
            'Fiber Tension': fi_ft,
            'Fiber Compression': fi_fc,
            'Matrix Tension': fi_mt,
            'Matrix Compression': fi_mc
        }
        
        max_fi = max(modes_fi.values())
        dominant_mode = max(modes_fi, key=modes_fi.get) if max_fi > 0 else "None"
        
        min_lam = min(lam_ft, lam_fc, lam_mt, lam_mc)
        mos = min_lam - 1.0 if min_lam != float('inf') else float('inf')
        
        # Check C > 1 edge case (Failed already purely due to thermal residual stresses)
        thermal_fail = C_ft > 1.0 or C_fc > 1.0 or C_mt > 1.0 or C_mc > 1.0
        
        return {
            'fiber_tension': fi_ft,
            'fiber_compression': fi_fc,
            'matrix_tension': fi_mt,
            'matrix_compression': fi_mc,
            'max_fi': max_fi,
            'dominant_mode': dominant_mode,
            'mos': mos,
            'thermal_fail': thermal_fail
        }

    @staticmethod
    def tsai_wu_criterion(sm: list, st: list, material: OrthotropicMaterial) -> dict:
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
        
        A_tw = F11*sm[0]**2 + F22*sm[1]**2 + F66*sm[2]**2 + 2*F12*sm[0]*sm[1]
        
        B_tw = (F1*sm[0] + F2*sm[1] + 
                2*F11*st[0]*sm[0] + 2*F22*st[1]*sm[1] + 2*F66*st[2]*sm[2] + 
                2*F12*(st[0]*sm[1] + sm[0]*st[1]))
                
        C_tw = (F1*st[0] + F2*st[1] + 
                F11*st[0]**2 + F22*st[1]**2 + F66*st[2]**2 + 
                2*F12*st[0]*st[1])
        
        fi = A_tw + B_tw + C_tw
        lams = FailureCriteriaEngine._solve_lambda(A_tw, B_tw, C_tw)
        lam = lams[0] if lams else float('inf')
        mos = lam - 1.0 if lam != float('inf') else float('inf')
        
        return {'fi': fi, 'mos': mos, 'thermal_fail': C_tw > 1.0}
    
    def evaluate_ply(self, sigma_mech: list, sigma_therm: list,
                     material: OrthotropicMaterial, ply_id: int, 
                     angle: float) -> FailureResult:
        """
        Bir katman için tüm kırılma kriterlerini hesaplar.
        """
        hashin = self.hashin_criteria(sigma_mech, sigma_therm, material)
        tsai_wu = self.tsai_wu_criterion(sigma_mech, sigma_therm, material)
        
        min_mos = min(hashin['mos'], tsai_wu['mos'])
        gov_crit = "Hashin" if hashin['mos'] <= tsai_wu['mos'] else "Tsai-Wu"
        
        # Eğer termal stresler tek başına kırılmaya yetiyorsa, mos negatif çıkar.
        is_failed = min_mos < 0.0
        
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
            mos_hashin=hashin['mos'],
            mos_tsai_wu=tsai_wu['mos'],
            min_mos=min_mos,
            governing_criterion=gov_crit,
            is_failed=is_failed
        )
