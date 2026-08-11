/**
 * AeroJoint V3.0 CAD & 3D Entegrasyon API İletişim Servisi (Fetch tabanlı).
 */

const API_BASE_URL = 'http://localhost:8000/api/cad';

export interface CadHole {
  id: number;
  name: string;
  center: [number, number, number];
  diameter: number;
  axis_vector: [number, number, number];
  normal_dot_product: number;
  is_perpendicular: boolean;
  surface_type: string;
}

export interface CurvatureProfile {
  gaussian_curvature: number;
  mean_curvature: number;
  radius_of_curvature: number;
  recommended_option: 'Option_1_Tangent_Plane' | 'Option_2_Geodesic' | 'Option_3_Kinematic_Draping';
  method_title: string;
  explanation: string;
}

export interface CadUploadResponse {
  filename: string;
  n_vertices: number;
  n_faces: number;
  width?: number;
  height?: number;
  thickness?: number;
  suggested_plies?: Array<{ material_id: string; angle: number; thickness: number }>;
  bounds: {
    min: [number, number, number];
    max: [number, number, number];
    dimensions: [number, number, number];
  };
  mesh_data: {
    vertices: number[][];
    faces: number[][];
    normals: number[][];
  };
  detected_holes: CadHole[];
  curvature_profile: CurvatureProfile;
}

export interface LoadMatchResult {
  matched_results: Array<{
    hole_id: number;
    hole_name: string;
    cad_center: [number, number, number];
    load_center: [number, number, number];
    diameter: number;
    distance_error_mm: number;
    force_vector: [number, number, number];
    magnitude: number;
    match_status: 'EXACT' | 'TOLERANCE_MATCH';
  }>;
  orphan_loads: Array<{
    load_id: string;
    coord: [number, number, number];
    force: [number, number, number];
    magnitude_in_plane: number;
  }>;
  unmatched_holes: CadHole[];
  summary: {
    total_holes: number;
    total_loads: number;
    matched_count: number;
    orphan_count: number;
    unassigned_holes_count: number;
    tolerance_used_mm: number;
    status: string;
  };
}

export const uploadCadFile = async (file: File): Promise<CadUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/upload-step`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('CAD yükleme hatası');
  return res.json();
};

export const matchFemLoads = async (
  file: File,
  cadHoles: CadHole[],
  toleranceMm: number = 2.0
): Promise<LoadMatchResult> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tolerance_mm', toleranceMm.toString());
  formData.append('cad_holes_json', JSON.stringify(cadHoles));

  const res = await fetch(`${API_BASE_URL}/match-loads`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('FEM yük eşleştirme hatası');
  return res.json();
};

export const transformForces = async (
  normalVector: [number, number, number],
  forceGlobal: [number, number, number]
) => {
  const res = await fetch(`${API_BASE_URL}/transform-forces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      normal_vector: normalVector,
      force_global: forceGlobal,
    }),
  });
  if (!res.ok) throw new Error('Kuvvet transformasyon hatası');
  return res.json();
};
