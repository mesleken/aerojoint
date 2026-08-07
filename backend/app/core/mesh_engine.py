"""
Gmsh Tabanlı Otomatik Geometri ve Mesh Motoru.

2 giriş modu (v1.0):
  1. Parametrik Form: Boyutlar ve delik koordinatları
  2. Koordinat Matrisi: [x_i, y_i, d_i] tablosu

v1.1'de eklenecek:
  3. DXF Import: ezdxf ile dış kontur (edge case riski nedeniyle ertelendi)

Mesh Stratejisi:
  - Q4 lineer elemanlar (birincil)
  - Delik çevresinde 4-6 katman radyal sıklaştırma (boundary layer)
  - Quad-dominant mesh (Blossom recombination)
  - Distance + Threshold field ile boyut geçişi
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

try:
    import gmsh
    HAS_GMSH = True
except ImportError:
    HAS_GMSH = False


@dataclass
class GeometryConfig:
    width: float
    height: float
    holes: List[Dict[str, float]]          # [{'x': ..., 'y': ..., 'diameter': ...}, ...]
    mesh_size_global: float = 3.0
    mesh_size_hole: float = 0.5
    boundary_layers: int = 4
    element_order: int = 1     # 1=Q4 (birincil), 2=Q8 (opsiyonel)


class MeshEngine:
    """Gmsh tabanlı otomatik geometri ve mesh motoru."""
    
    def create_mesh(self, config: GeometryConfig) -> Dict[str, Any]:
        if not HAS_GMSH:
            raise ImportError(
                "Gmsh kütüphanesi yüklü değil. Lütfen 'pip install gmsh' çalıştırın."
            )

        import signal
        orig_signal = signal.signal
        try:
            signal.signal = lambda *args, **kwargs: None
        except Exception:
            pass

        try:
            gmsh.initialize()
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.model.add("composite_plate")
            
            # Dikdörtgen plaka
            plate_tag = gmsh.model.occ.addRectangle(
                0, 0, 0, config.width, config.height
            )
            
            # Delikleri Boolean Cut ile kes
            hole_disk_tags = []
            for hole in config.holes:
                disk = gmsh.model.occ.addDisk(
                    hole['x'], hole['y'], 0,
                    hole['diameter'] / 2.0, hole['diameter'] / 2.0
                )
                hole_disk_tags.append((2, disk))
            
            if hole_disk_tags:
                gmsh.model.occ.cut(
                    [(2, plate_tag)], hole_disk_tags,
                    removeObject=True, removeTool=True
                )
            
            gmsh.model.occ.synchronize()
            self._setup_mesh_fields(config)
            self._configure_mesh_options(config)
            
            gmsh.model.mesh.generate(2)
            if config.element_order == 2:
                gmsh.model.mesh.setOrder(2)
            
            return self._extract_mesh_data(config)
        finally:
            if gmsh.isInitialized():
                gmsh.finalize()
    
    def _setup_mesh_fields(self, config: GeometryConfig):
        """Delik çevresinde Distance + Threshold + BoundaryLayer field."""
        surfaces = gmsh.model.getEntities(2)
        curves = gmsh.model.getBoundary(surfaces, combined=False, oriented=False)
        
        hole_curves = []
        for dim, tag in curves:
            try:
                if 'Circle' in gmsh.model.getType(dim, tag):
                    hole_curves.append(tag)
            except Exception:
                pass
        
        if not hole_curves:
            return
        
        f_dist = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(f_dist, "CurvesList", hole_curves)
        gmsh.model.mesh.field.setNumber(f_dist, "Sampling", 100)
        
        f_thresh = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(f_thresh, "InField", f_dist)
        gmsh.model.mesh.field.setNumber(f_thresh, "SizeMin", config.mesh_size_hole)
        gmsh.model.mesh.field.setNumber(f_thresh, "SizeMax", config.mesh_size_global)
        gmsh.model.mesh.field.setNumber(f_thresh, "DistMin", 0.0)
        
        max_d = max(h['diameter'] for h in config.holes) if config.holes else 10.0
        gmsh.model.mesh.field.setNumber(f_thresh, "DistMax", max_d * 3)
        gmsh.model.mesh.field.setAsBackgroundMesh(f_thresh)
        
        if config.boundary_layers > 0:
            f_bl = gmsh.model.mesh.field.add("BoundaryLayer")
            gmsh.model.mesh.field.setNumbers(f_bl, "CurvesList", hole_curves)
            gmsh.model.mesh.field.setNumber(f_bl, "Size", config.mesh_size_hole)
            gmsh.model.mesh.field.setNumber(f_bl, "Ratio", 1.3)
            gmsh.model.mesh.field.setNumber(f_bl, "NbLayers", config.boundary_layers)
            gmsh.model.mesh.field.setNumber(f_bl, "Quads", 1)
    
    def _configure_mesh_options(self, config: GeometryConfig):
        """Quad-dominant meshing."""
        gmsh.option.setNumber("Mesh.Algorithm", 8)        # Frontal-Delaunay for Quads
        gmsh.option.setNumber("Mesh.RecombineAll", 1)
        gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)  # Blossom
        gmsh.option.setNumber("Mesh.Smoothing", 10)
        gmsh.option.setNumber("Mesh.ElementOrder", config.element_order)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", config.mesh_size_global)
    
    def _extract_mesh_data(self, config: GeometryConfig) -> Dict[str, Any]:
        """Gmsh'ten mesh verisini çıkar."""
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        node_coords = node_coords.reshape(-1, 3)[:, :2]
        tag_to_idx = {int(tag): i for i, tag in enumerate(node_tags)}
        
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim=2)
        elements_list = []
        elem_type_name = 'Q4'
        
        for etype, etags, enodes in zip(elem_types, elem_tags, elem_node_tags):
            props = gmsh.model.mesh.getElementProperties(etype)
            n_per = props[3]
            elem_type_name = 'Q4' if n_per == 4 else ('Q8' if n_per == 8 else 'T3')
            enodes = enodes.reshape(-1, n_per)
            for row in enodes:
                elements_list.append([tag_to_idx[int(n)] for n in row])
        
        nodes = node_coords
        elements = np.array(elements_list) if elements_list else np.empty((0, 4), dtype=int)
        
        # Sınır düğümleri
        boundary = self._identify_boundary_nodes(nodes, config)
        
        return {
            'nodes': nodes, 'elements': elements,
            'element_type': elem_type_name,
            'boundary_nodes': boundary,
            'hole_boundary_nodes': boundary.get('holes', []),
            'statistics': {
                'n_nodes': len(nodes), 'n_elements': len(elements),
                'n_dof': 2 * len(nodes), 'element_type': elem_type_name
            }
        }
    
    def _identify_boundary_nodes(self, nodes: np.ndarray, config: GeometryConfig) -> Dict[str, Any]:
        tol_plate = max(config.mesh_size_global * 0.25, 0.5)
        tol_hole = max(config.mesh_size_hole * 0.4, 0.5)
        boundary: Dict[str, Any] = {'left': [], 'right': [], 'bottom': [], 'top': [], 'holes': []}
        
        for i, (x, y) in enumerate(nodes):
            if abs(x) <= tol_plate: boundary['left'].append(i)
            if abs(x - config.width) <= tol_plate: boundary['right'].append(i)
            if abs(y) <= tol_plate: boundary['bottom'].append(i)
            if abs(y - config.height) <= tol_plate: boundary['top'].append(i)
        
        for h_idx, hole in enumerate(config.holes):
            cx, cy, r = hole['x'], hole['y'], hole['diameter'] / 2.0
            hole_nodes = []
            for i, (x, y) in enumerate(nodes):
                dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                if abs(dist - r) <= tol_hole:
                    hole_nodes.append({'id': i, 'x': float(x), 'y': float(y)})
            boundary['holes'].append({
                'hole_id': h_idx, 'center': (hole['x'], hole['y']),
                'diameter': hole['diameter'], 'nodes': hole_nodes
            })
        
        return boundary
