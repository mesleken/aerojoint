import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { PlyInput, HoleInput, AnalysisResponse, MaterialOption } from '../types/analysis';

interface AnalysisState {
  // Modal states
  isMaterialModalOpen: boolean;
  isCadModalOpen: boolean;
  setIsMaterialModalOpen: (open: boolean) => void;
  setIsCadModalOpen: (open: boolean) => void;

  // Materials list
  materials: MaterialOption[];
  setMaterials: (materials: MaterialOption[]) => void;

  // Analysis geometry & parameters
  plies: PlyInput[];
  width: number;
  height: number;
  holes: HoleInput[];
  constraintType: string;
  meshGlobal: number;
  meshHole: number;
  enablePDM: boolean;
  failureCriterion: string;

  // Parameter setters
  setPlies: (plies: PlyInput[]) => void;
  setWidth: (width: number) => void;
  setHeight: (height: number) => void;
  setHoles: (holes: HoleInput[]) => void;
  setConstraintType: (type: string) => void;
  setMeshGlobal: (val: number) => void;
  setMeshHole: (val: number) => void;
  setEnablePDM: (enable: boolean) => void;
  setFailureCriterion: (criterion: string) => void;

  // Results & UI State
  results: AnalysisResponse | null;
  loading: boolean;
  error: string | null;
  stressComponent: 'sigma_x' | 'sigma_y' | 'tau_xy' | 'von_mises' | 'hashin_fi';

  setResults: (results: AnalysisResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setStressComponent: (comp: 'sigma_x' | 'sigma_y' | 'tau_xy' | 'von_mises' | 'hashin_fi') => void;

  // CAD integration action
  applyCadData: (params: {
    width?: number;
    height?: number;
    holes: Array<{ x: number; y: number; diameter: number; load_magnitude: number }>;
    plies?: Array<{ material_id: string; angle: number; thickness: number }>;
  }) => void;
  applyCadHoles: (newHoles: Array<{ x: number; y: number; diameter: number; load_magnitude: number }>) => void;
  resetToDefaults: () => void;
}

const DEFAULT_PLIES: PlyInput[] = [
  { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 90, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 90, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 90, thickness: 0.125 },
  { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 90, thickness: 0.125 },
  { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
  { material_id: 'T300_5208', angle: 0, thickness: 0.125 }
];

const DEFAULT_HOLES: HoleInput[] = [
  { x: 60, y: 50, diameter: 6.35, load_magnitude: 1500, load_angle: 0, torque: 0 }
];

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      isMaterialModalOpen: false,
      isCadModalOpen: false,
      setIsMaterialModalOpen: (open) => set({ isMaterialModalOpen: open }),
      setIsCadModalOpen: (open) => set({ isCadModalOpen: open }),

      materials: [],
      setMaterials: (materials) => set({ materials }),

      plies: DEFAULT_PLIES,
      width: 200,
      height: 100,
      holes: DEFAULT_HOLES,
      constraintType: 'fixed',
      meshGlobal: 4.0,
      meshHole: 0.5,
      enablePDM: false,
      failureCriterion: 'Hashin',

      setPlies: (plies) => set({ plies }),
      setWidth: (width) => set({ width }),
      setHeight: (height) => set({ height }),
      setHoles: (holes) => set({ holes }),
      setConstraintType: (constraintType) => set({ constraintType }),
      setMeshGlobal: (meshGlobal) => set({ meshGlobal }),
      setMeshHole: (meshHole) => set({ meshHole }),
      setEnablePDM: (enablePDM) => set({ enablePDM }),
      setFailureCriterion: (failureCriterion) => set({ failureCriterion }),

      results: null,
      loading: false,
      error: null,
      stressComponent: 'von_mises',

      setResults: (results) => set({ results }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setStressComponent: (stressComponent) => set({ stressComponent }),

      applyCadData: (params) => {
        const formatted: HoleInput[] = params.holes.map((h) => ({
          x: h.x,
          y: h.y,
          diameter: h.diameter,
          load_magnitude: h.load_magnitude,
          load_angle: 0,
          torque: 0,
        }));
        
        const updates: Partial<AnalysisState> = { holes: formatted };
        if (params.width && params.width > 0) updates.width = params.width;
        if (params.height && params.height > 0) updates.height = params.height;
        if (params.plies && params.plies.length > 0) updates.plies = params.plies;

        set(updates as any);
      },

      applyCadHoles: (newHoles) => {
        const formatted: HoleInput[] = newHoles.map((h) => ({
          x: h.x,
          y: h.y,
          diameter: h.diameter,
          load_magnitude: h.load_magnitude,
          load_angle: 0,
          torque: 0,
        }));
        set({ holes: formatted });
      },

      resetToDefaults: () => set({
        plies: DEFAULT_PLIES,
        width: 200,
        height: 100,
        holes: DEFAULT_HOLES,
        constraintType: 'fixed',
        meshGlobal: 6.0,
        meshHole: 1.2,
        enablePDM: false,
        failureCriterion: 'Hashin',
        results: null,
        error: null
      })
    }),
    {
      name: 'aerojoint-analysis-session-v4',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        plies: state.plies,
        width: state.width,
        height: state.height,
        holes: state.holes,
        constraintType: state.constraintType,
        meshGlobal: state.meshGlobal,
        meshHole: state.meshHole,
        enablePDM: state.enablePDM,
        failureCriterion: state.failureCriterion,
        stressComponent: state.stressComponent,
      }),
    }
  )
);
