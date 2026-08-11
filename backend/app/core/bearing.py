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
    clearance: float = 0.0  # mm, pim-delik boşluğu (tolerans)


class BearingPressureModel:
    
    def apply_bearing_loads(self, bearing_load: BearingLoad,
                            hole_boundary_nodes: list[dict],
                            thickness: float) -> dict:
        """
        Delik sınır düğümlerine adaptif kosinüs dağılımlı nodal kuvvetler uygula.
        Pim-delik boşluğu (clearance c) için standart Hertzian/CMH-17 temas mekaniği:
          - c = 0.00 mm -> Temas yarı açısı θc = 90.0° (π/2)
          - c = 0.05 mm -> Temas yarı açısı θc = 67.5° (3π/8)
          - c >= 0.10 mm -> Maksimum daralma θc = 45.0° (π/4)
        """
        P = bearing_load.load_magnitude
        D = bearing_load.diameter
        R = D / 2.0
        cx, cy = bearing_load.hole_x, bearing_load.hole_y
        alpha = np.radians(bearing_load.load_angle)
        
        # Clearance c > 0 ise temas açısı (contact angle) Hertzian formülasyonuyla daralır
        c = bearing_load.clearance
        theta_c = np.pi / 2.0
        if c > 0:
            reduction_factor = min(1.0, c / 0.1) # c >= 0.1mm için maksimum %50 daralma
            theta_c = (np.pi / 2.0) * (1.0 - reduction_factor * 0.5) # Minimum 45° (pi/4)
            
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
        
        rel_forces = {}
        total_F_bearing = 0.0
        
        for i, node in enumerate(nodes_sorted):
            theta = node['theta']
            
            if abs(theta) > theta_c:
                rel_forces[node['id']] = (0.0, 0.0)
                continue
            
            i_prev = (i - 1) % n_nodes
            i_next = (i + 1) % n_nodes
            
            dphi_prev = nodes_sorted[i]['phi'] - nodes_sorted[i_prev]['phi']
            dphi_next = nodes_sorted[i_next]['phi'] - nodes_sorted[i]['phi']
            
            if dphi_prev < -np.pi: dphi_prev += 2 * np.pi
            if dphi_prev > np.pi: dphi_prev -= 2 * np.pi
            if dphi_next < -np.pi: dphi_next += 2 * np.pi
            if dphi_next > np.pi: dphi_next -= 2 * np.pi
            
            delta_arc = R * (abs(dphi_prev) + abs(dphi_next)) / 2.0
            
            # Adaptif kosinüs formu: cos( (pi/2) * (theta / theta_c) )
            pressure_rel = np.cos((np.pi / 2.0) * (theta / theta_c))
            Fr_rel = pressure_rel * thickness * delta_arc
            
            phi = node['phi']
            Fx_rel = Fr_rel * np.cos(phi)
            Fy_rel = Fr_rel * np.sin(phi)
            
            rel_forces[node['id']] = (Fx_rel, Fy_rel)
            
            # Yük yönündeki taşıma kuvvetini topla
            total_F_bearing += (Fx_rel * np.cos(alpha) + Fy_rel * np.sin(alpha))
            
        nodal_forces = {}
        # Yük denkleştirme faktörü
        scale_factor = P / total_F_bearing if total_F_bearing > 1e-9 else 0.0
        
        for nid, (fx_r, fy_r) in rel_forces.items():
            nodal_forces[nid] = (fx_r * scale_factor, fy_r * scale_factor)
            
        return nodal_forces
