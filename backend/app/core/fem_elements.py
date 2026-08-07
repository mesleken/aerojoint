"""
Sonlu Eleman Formülasyonları.
Q4 (4 Düğümlü Lineer İzoparametrik Dörtgen)
"""
import numpy as np


class Q4Element:
    """4 Düğümlü İzoparametrik Dörtgen Eleman."""
    
    GP = 1.0 / np.sqrt(3.0)
    GAUSS_POINTS = [(-GP, -GP), (GP, -GP), (GP, GP), (-GP, GP)]
    GAUSS_WEIGHTS = [1.0, 1.0, 1.0, 1.0]
    N_NODES = 4
    N_DOF = 8  # 4 düğüm × 2 DOF
    
    @staticmethod
    def shape_functions(xi: float, eta: float) -> np.ndarray:
        """N₁..N₄ şekil fonksiyonları."""
        return 0.25 * np.array([
            (1 - xi) * (1 - eta),
            (1 + xi) * (1 - eta),
            (1 + xi) * (1 + eta),
            (1 - xi) * (1 + eta)
        ])
    
    @staticmethod
    def shape_function_derivatives(xi: float, eta: float) -> np.ndarray:
        """dN/dξ ve dN/dη (2×4 matris)."""
        return 0.25 * np.array([
            [-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],
            [-(1 - xi), -(1 + xi), (1 + xi),   (1 - xi)]
        ])
    
    @classmethod
    def stiffness_matrix(cls, xe: np.ndarray, ye: np.ndarray,
                          C: np.ndarray, thickness: float) -> np.ndarray:
        """
        [Kₑ] = t · ∫∫ [B]ᵀ [C] [B] |det(J)| dξ dη
        """
        Ke = np.zeros((8, 8))
        
        for (xi, eta), w in zip(cls.GAUSS_POINTS, cls.GAUSS_WEIGHTS):
            dN = cls.shape_function_derivatives(xi, eta)
            J = dN @ np.column_stack([xe, ye])
            detJ = np.linalg.det(J)
            
            if detJ <= 0:
                raise ValueError(f"Negatif Jacobian ({detJ:.4f}). Düğüm sırası kontrol edin.")
            
            dN_dxy = np.linalg.inv(J) @ dN
            
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]     = dN_dxy[0, i]   # εx
                B[1, 2*i + 1] = dN_dxy[1, i]   # εy
                B[2, 2*i]     = dN_dxy[1, i]   # γxy
                B[2, 2*i + 1] = dN_dxy[0, i]   # γxy
            
            Ke += w * thickness * (B.T @ C @ B) * detJ
        
        return Ke
    
    @classmethod
    def compute_stress(cls, xe: np.ndarray, ye: np.ndarray,
                        ue: np.ndarray, C: np.ndarray) -> np.ndarray:
        """Gauss noktalarındaki gerilmeler: σ = C · B · uₑ"""
        stresses = []
        for (xi, eta), _ in zip(cls.GAUSS_POINTS, cls.GAUSS_WEIGHTS):
            dN = cls.shape_function_derivatives(xi, eta)
            J = dN @ np.column_stack([xe, ye])
            dN_dxy = np.linalg.inv(J) @ dN
            
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]     = dN_dxy[0, i]
                B[1, 2*i + 1] = dN_dxy[1, i]
                B[2, 2*i]     = dN_dxy[1, i]
                B[2, 2*i + 1] = dN_dxy[0, i]
            
            stresses.append(C @ B @ ue)
        
        return np.array(stresses)
