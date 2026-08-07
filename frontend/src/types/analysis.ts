export interface PlyInput {
  material_id: string;
  angle: number;
  thickness: number;
}

export interface HoleInput {
  x: number;
  y: number;
  diameter: number;
  load_magnitude: number;
  load_angle: number;
}

export interface AnalysisRequest {
  width: number;
  height: number;
  plies: PlyInput[];
  holes: HoleInput[];
  constraint_type: string;
  mesh_size_global: number;
  mesh_size_hole: number;
}

export interface PlyResult {
  ply_id: number;
  angle: number;
  hashin_max_fi: number;
  dominant_mode: string;
  tsai_wu_fi: number;
  mos_hashin: number;
  is_failed: boolean;
}

export interface AnalysisResponse {
  layup_notation: string;
  total_thickness: number;
  min_mos: number;
  overall_status: 'PASS' | 'FAIL';
  governing_criterion: string;
  critical_ply: number;
  critical_angle: number;
  critical_mode: string;
  ply_results: PlyResult[];
  A_matrix: number[][];
  B_matrix: number[][];
  D_matrix: number[][];
  B_nonzero: boolean;
  applied_load: number;
  computation_time_ms: number;
  mesh_summary: {
    n_nodes: number;
    n_elements: number;
    n_dof: number;
    element_type: string;
  };
  nodes: number[][];
  elements: number[][];
  nodal_stresses: number[][];
}

export interface MaterialOption {
  id: string;
  name: string;
  category: string;
  source: string;
  ply_thickness: number;
}
