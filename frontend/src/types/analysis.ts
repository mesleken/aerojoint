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
  torque?: number; // Cıvata Sıkma Torku (Nm)
}

export interface LoadCase {
  name: string;
  magnitude: number;
  angle: number;
}

export interface AnalysisRequest {
  width: number;
  height: number;
  plies: PlyInput[];
  holes: HoleInput[];
  constraint_type: string;
  mesh_size_global: number;
  mesh_size_hole: number;
  enable_pdm?: boolean; // Progressive Damage Modeling
  failure_criterion?: 'Hashin' | 'Tsai-Wu' | 'Puck';
  load_cases?: LoadCase[];
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

export interface PDMStep {
  step: number;
  load_factor: number;
  load_N: number;
  failed_matrix_elements: number;
  failed_fiber_elements: number;
  status: string;
}

export interface ProgressiveDamageResult {
  ultimate_load_N: number;
  first_ply_failure_load_N: number;
  ultimate_bearing_stress_MPa: number;
  history: PDMStep[];
  is_ultimate_failed: boolean;
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
  nodal_hashin_fi?: number[];
  pdm_results?: ProgressiveDamageResult;
  stress_frames?: number[][][]; // Multi-step animation stress states
  envelope_results?: any;
}

export interface MaterialOption {
  id: string;
  name: string;
  category: string;
  source: string;
  ply_thickness: number;
}

export interface CustomMaterialPayload {
  id: string;
  name: string;
  category?: string;
  source?: string;
  ply_thickness: number;
  elastic: {
    E1: number;
    E2: number;
    G12: number;
    nu12: number;
  };
  strength: {
    Xt: number;
    Xc: number;
    Yt: number;
    Yc: number;
    S12: number;
    S23?: number;
  };
}
