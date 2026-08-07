import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class OrthotropicMaterial:
    """Tek yönlü (UD) kompozit katman malzeme özellikleri."""
    name: str
    E1: float          # Elyaf doğrultusunda elastisite modülü (MPa)
    E2: float          # Elyafa dik elastisite modülü (MPa)
    G12: float         # Düzlem-içi kayma modülü (MPa)
    nu12: float        # Majör Poisson oranı
    
    # Mukavemet sınırları (Allowables) — pozitif değerler
    Xt: float          # Elyaf yönü çekme mukavemeti (MPa)
    Xc: float          # Elyaf yönü basma mukavemeti (MPa)
    Yt: float          # Elyafa dik çekme mukavemeti (MPa)
    Yc: float          # Elyafa dik basma mukavemeti (MPa)
    S12: float         # Düzlem-içi kayma mukavemeti (MPa)
    S23: Optional[float] = None  # Enine kayma mukavemeti (opsiyonel)
    
    @property
    def nu21(self) -> float:
        """Karşılıklılık ilişkisinden hesaplanan minör Poisson oranı."""
        return self.nu12 * self.E2 / self.E1
    
    def validate(self) -> bool:
        """Malzeme tutarlılık kontrolü."""
        assert self.E1 > 0 and self.E2 > 0 and self.G12 > 0
        assert 0 < self.nu12 < 1
        assert self.nu12 * self.nu21 < 1, "Termodinamik tutarlılık: nu12*nu21 < 1"
        return True


@dataclass
class Ply:
    """Tek bir kompozit katman."""
    material: OrthotropicMaterial
    angle: float           # Elyaf açısı (derece)
    thickness: float       # Katman kalınlığı (mm)
    ply_id: int = 0


@dataclass
class Laminate:
    """Çok katmanlı kompozit laminat dizilimi."""
    plies: List[Ply]
    
    @property
    def total_thickness(self) -> float:
        return sum(ply.thickness for ply in self.plies)
    
    @property
    def n_plies(self) -> int:
        return len(self.plies)
    
    @property
    def is_symmetric(self) -> bool:
        """Simetri kontrolü: dizilim orta düzleme göre simetrik mi?"""
        n = self.n_plies
        for i in range(n // 2):
            if (self.plies[i].angle != self.plies[n - 1 - i].angle or
                self.plies[i].thickness != self.plies[n - 1 - i].thickness):
                return False
        return True
    
    @property
    def layup_notation(self) -> str:
        """İnsan okunabilir katman notasyonu üret. Örn: [0₂/±45₂/90]s"""
        # Basitleştirilmiş notasyon
        angles = [ply.angle for ply in self.plies]
        if self.is_symmetric:
            half = angles[:self.n_plies // 2]
            return f"[{'/'.join(str(int(a)) + '°' for a in half)}]s"
        return f"[{'/'.join(str(int(a)) + '°' for a in angles)}]"
    
    def get_z_coordinates(self) -> List[float]:
        """Her katmanın alt ve üst z koordinatlarını hesapla (orta düzlemden)."""
        h = self.total_thickness
        z = [-h / 2]
        for ply in self.plies:
            z.append(z[-1] + ply.thickness)
        return z

class CLTEngine:
    """
    Klasik Laminat Teorisi hesap motoru.
    
    Hesap akışı:
    1. Her katman için [Q] → [Q̄(θ)] hesapla
    2. z koordinatları üzerinden [A], [B], [D] biriktir
    3. ABD⁻¹ ile orta düzlem gerinim ve eğrilikleri çöz
    4. Her katmanın alt/orta/üst noktasında σ₁, σ₂, τ₁₂ hesapla
    """
    
    @staticmethod
    def compute_Q(material: OrthotropicMaterial) -> np.ndarray:
        """
        On-axis indirilmiş rijitlik matrisi [Q] (3×3).
        
        Q₁₁ = E₁/(1-ν₁₂·ν₂₁)
        Q₂₂ = E₂/(1-ν₁₂·ν₂₁)
        Q₁₂ = ν₁₂·E₂/(1-ν₁₂·ν₂₁)
        Q₆₆ = G₁₂
        """
        E1, E2 = material.E1, material.E2
        nu12, nu21 = material.nu12, material.nu21
        G12 = material.G12
        
        denom = 1.0 - nu12 * nu21
        
        Q = np.array([
            [E1 / denom,       nu12 * E2 / denom, 0.0],
            [nu12 * E2 / denom, E2 / denom,        0.0],
            [0.0,               0.0,                G12]
        ])
        return Q
    
    @staticmethod
    def compute_Qbar(Q: np.ndarray, theta_deg: float) -> np.ndarray:
        """
        Dönüştürülmüş rijitlik matrisi [Q̄] (3×3).
        
        Açık formüller ile hesaplanır (dönüşüm matrisi yerine doğrudan).
        """
        theta = np.radians(theta_deg)
        m = np.cos(theta)
        n = np.sin(theta)
        
        m2, n2, mn = m**2, n**2, m * n
        m4, n4 = m**4, n**4
        m2n2 = m2 * n2
        
        Q11, Q12, Q22, Q66 = Q[0,0], Q[0,1], Q[1,1], Q[2,2]
        
        Qbar = np.zeros((3, 3))
        Qbar[0,0] = Q11*m4 + 2*(Q12 + 2*Q66)*m2n2 + Q22*n4
        Qbar[0,1] = (Q11 + Q22 - 4*Q66)*m2n2 + Q12*(m4 + n4)
        Qbar[1,0] = Qbar[0,1]
        Qbar[1,1] = Q11*n4 + 2*(Q12 + 2*Q66)*m2n2 + Q22*m4
        Qbar[0,2] = (Q11 - Q12 - 2*Q66)*m**3*n - (Q22 - Q12 - 2*Q66)*m*n**3
        Qbar[2,0] = Qbar[0,2]
        Qbar[1,2] = (Q11 - Q12 - 2*Q66)*m*n**3 - (Q22 - Q12 - 2*Q66)*m**3*n
        Qbar[2,1] = Qbar[1,2]
        Qbar[2,2] = (Q11 + Q22 - 2*Q12 - 2*Q66)*m2n2 + Q66*(m4 + n4)
        
        return Qbar
    
    @staticmethod
    def compute_ABD(laminate: Laminate) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        [A], [B], [D] rijitlik matrislerini hesapla.
        
        A_ij = Σₖ Q̄_ij(k) × (zₖ - zₖ₋₁)
        B_ij = ½ Σₖ Q̄_ij(k) × (zₖ² - zₖ₋₁²)
        D_ij = ⅓ Σₖ Q̄_ij(k) × (zₖ³ - zₖ₋₁³)
        """
        A = np.zeros((3, 3))
        B = np.zeros((3, 3))
        D = np.zeros((3, 3))
        
        z_coords = laminate.get_z_coordinates()
        engine = CLTEngine()
        
        for k, ply in enumerate(laminate.plies):
            z_bot = z_coords[k]
            z_top = z_coords[k + 1]
            
            Q = engine.compute_Q(ply.material)
            Qbar = engine.compute_Qbar(Q, ply.angle)
            
            A += Qbar * (z_top - z_bot)
            B += 0.5 * Qbar * (z_top**2 - z_bot**2)
            D += (1.0/3.0) * Qbar * (z_top**3 - z_bot**3)
        
        return A, B, D
    
    @staticmethod
    def compute_ABD_inverse(A, B, D) -> np.ndarray:
        """ABD matrisinin tersini al → 6×6 uyum matrisi."""
        ABD = np.block([[A, B], [B, D]])
        return np.linalg.inv(ABD)
    
    @staticmethod
    def transform_stress_to_local(sigma_global: np.ndarray, 
                                   theta_deg: float) -> np.ndarray:
        """
        Global gerilmeleri (σx, σy, τxy) → malzeme koordinatlarına (σ₁, σ₂, τ₁₂).
        {σ_local} = [T(θ)] {σ_global}
        """
        theta = np.radians(theta_deg)
        m = np.cos(theta)
        n = np.sin(theta)
        
        T = np.array([
            [ m**2,  n**2,   2*m*n],
            [ n**2,  m**2,  -2*m*n],
            [-m*n,   m*n,    m**2 - n**2]
        ])
        return T @ sigma_global
    
    @staticmethod
    def compute_ply_stresses(laminate: Laminate, 
                              N: np.ndarray,
                              M: np.ndarray) -> list[dict]:
        """
        Her katmandaki gerilmeleri hesapla.
        
        Adımlar:
        1. ABD⁻¹ ile orta düzlem gerinim ve eğrilikleri çöz
        2. Her katmanın alt/orta/üst z noktasında global gerinimleri hesapla
        3. Q̄ ile global gerilmelere dönüştür
        4. T(θ) ile malzeme koordinatlarına (σ₁, σ₂, τ₁₂) dönüştür
        """
        engine = CLTEngine()
        A, B, D = engine.compute_ABD(laminate)
        abd_inv = engine.compute_ABD_inverse(A, B, D)
        
        load_vector = np.concatenate([N, M])
        deformation = abd_inv @ load_vector
        epsilon_0 = deformation[:3]
        kappa = deformation[3:]
        
        z_coords = laminate.get_z_coordinates()
        results = []
        
        for k, ply in enumerate(laminate.plies):
            z_bot = z_coords[k]
            z_top = z_coords[k + 1]
            z_mid = (z_bot + z_top) / 2.0
            
            Q = engine.compute_Q(ply.material)
            Qbar = engine.compute_Qbar(Q, ply.angle)
            
            ply_result = {'ply_id': k, 'angle': ply.angle, 'positions': {}}
            
            for label, z in [('bottom', z_bot), ('middle', z_mid), ('top', z_top)]:
                epsilon_global = epsilon_0 + z * kappa
                sigma_global = Qbar @ epsilon_global
                sigma_local = engine.transform_stress_to_local(sigma_global, ply.angle)
                
                ply_result['positions'][label] = {
                    'epsilon_global': epsilon_global.tolist(),
                    'sigma_global': sigma_global.tolist(),
                    'sigma_local': sigma_local.tolist(),
                    'z': z
                }
            
            results.append(ply_result)
        
        return results
