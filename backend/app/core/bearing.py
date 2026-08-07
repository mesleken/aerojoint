"""
Havacılık Standardı: Kosinüs Dağılımlı Radyal Basınç Modeli.
"""
import numpy as np
from dataclasses import dataclass

@dataclass
class BearingLoad:
    """Tek bir delik üzerindeki yataklama yükü tanımı."""
    hole_x: float
    hole_y: float
    diameter: float
    load_magnitude: float
    load_angle: float  # derece, x-ekseni pozitif yönden


class BearingPressureModel:
    
    @staticmethod
    def compute_peak_pressure(load: float, diameter: float, 
                               thickness: float) -> float:
        """p₀ = 4P / (π·D·t)"""
        return (4.0 * load) / (np.pi * diameter * thickness)
    
    @staticmethod
    def compute_average_bearing_stress(load: float, diameter: float,
                                        thickness: float) -> float:
        """σ_br = P / (D·t)"""
        return load / (diameter * thickness)
    
    def apply_bearing_loads(self, bearing_load: BearingLoad,
                            hole_boundary_nodes: list[dict],
                            thickness: float) -> dict:
        """
        Delik sınır düğümlerine kosinüs dağılımlı nodal kuvvetler uygula.
        
        Returns: {'node_id': (Fx, Fy), ...}
        """
        P = bearing_load.load_magnitude
        D = bearing_load.diameter
        R = D / 2.0
        cx, cy = bearing_load.hole_x, bearing_load.hole_y
        alpha = np.radians(bearing_load.load_angle)
        
        p0 = self.compute_peak_pressure(P, D, thickness)
        
        # Düğümlerin açısal pozisyonlarını hesapla
        nodes_sorted = []
        for node in hole_boundary_nodes:
            dx = node['x'] - cx
            dy = node['y'] - cy
            phi = np.arctan2(dy, dx)
            theta = np.arctan2(np.sin(phi - alpha), np.cos(phi - alpha))
            nodes_sorted.append({
                'id': node['id'], 'x': node['x'], 'y': node['y'],
                'phi': phi, 'theta': theta
            })
        
        nodes_sorted.sort(key=lambda n: n['phi'])
        n_nodes = len(nodes_sorted)
        nodal_forces = {}
        
        for i, node in enumerate(nodes_sorted):
            theta = node['theta']
            
            if abs(theta) > np.pi / 2:
                nodal_forces[node['id']] = (0.0, 0.0)
                continue
            
            # Tributary arc length
            i_prev = (i - 1) % n_nodes
            i_next = (i + 1) % n_nodes
            
            dphi_prev = nodes_sorted[i]['phi'] - nodes_sorted[i_prev]['phi']
            dphi_next = nodes_sorted[i_next]['phi'] - nodes_sorted[i]['phi']
            
            if dphi_prev < -np.pi: dphi_prev += 2 * np.pi
            if dphi_prev > np.pi: dphi_prev -= 2 * np.pi
            if dphi_next < -np.pi: dphi_next += 2 * np.pi
            if dphi_next > np.pi: dphi_next -= 2 * np.pi
            
            delta_arc = R * (abs(dphi_prev) + abs(dphi_next)) / 2.0
            
            pressure = p0 * np.cos(theta)
            Fr = pressure * thickness * delta_arc
            
            phi = node['phi']
            Fx = Fr * np.cos(phi)
            Fy = Fr * np.sin(phi)
            
            nodal_forces[node['id']] = (Fx, Fy)
        
        return nodal_forces
