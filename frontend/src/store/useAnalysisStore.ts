import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { PlyInput, HoleInput, AnalysisResponse, MaterialOption } from '../types/analysis';

export interface AuditRecord {
  id: string;
  timestamp: string;
  engineVersion: string;
  layupNotation: string;
  width: number;
  height: number;
  appliedLoad: number;
  minMos: number;
  overallStatus: 'PASS' | 'FAIL';
  governingCriterion: string;
  results: AnalysisResponse;
}

interface AnalysisState {
  // Modal states
  isMaterialModalOpen: boolean;
  isCadModalOpen: boolean;
  isHistoryModalOpen: boolean;
  setIsMaterialModalOpen: (open: boolean) => void;
  setIsCadModalOpen: (open: boolean) => void;
  setIsHistoryModalOpen: (open: boolean) => void;

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
  bypassLoad: number;

  // Audit history & saved runs
  analysisHistory: AuditRecord[];
  addAuditRecord: (record: AuditRecord) => void;

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
  setBypassLoad: (val: number) => void;

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
  applyTemplate: (templateName: 'NASA_QI' | 'TENSION_DOMINATED' | 'DUAL_HOLE') => void;
  getValidationErrors: () => string[];
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
    (set, get) => ({
      isMaterialModalOpen: false,
      isCadModalOpen: false,
      isHistoryModalOpen: false,
      setIsMaterialModalOpen: (open) => set({ isMaterialModalOpen: open }),
      setIsCadModalOpen: (open) => set({ isCadModalOpen: open }),
      setIsHistoryModalOpen: (open) => set({ isHistoryModalOpen: open }),

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
      bypassLoad: 0,

      analysisHistory: [],
      addAuditRecord: (record) => set((state) => ({
        analysisHistory: [record, ...state.analysisHistory.slice(0, 19)]
      })),

      setPlies: (plies) => set({ plies }),
      setWidth: (width) => set({ width }),
      setHeight: (height) => set({ height }),
      setHoles: (holes) => set({ holes }),
      setConstraintType: (constraintType) => set({ constraintType }),
      setMeshGlobal: (meshGlobal) => set({ meshGlobal }),
      setMeshHole: (meshHole) => set({ meshHole }),
      setEnablePDM: (enablePDM) => set({ enablePDM }),
      setFailureCriterion: (failureCriterion) => set({ failureCriterion }),
      setBypassLoad: (bypassLoad) => set({ bypassLoad }),

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

      applyTemplate: (templateName) => {
        if (templateName === 'NASA_QI') {
          set({
            width: 150,
            height: 80,
            holes: [{ x: 50, y: 40, diameter: 6.35, load_magnitude: 4445, load_angle: 0, torque: 0 }],
            plies: [
              { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 90, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 90, thickness: 0.125 },
              { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 0, thickness: 0.125 }
            ]
          });
        } else if (templateName === 'TENSION_DOMINATED') {
          set({
            width: 220,
            height: 110,
            holes: [{ x: 70, y: 55, diameter: 8.0, load_magnitude: 8500, load_angle: 0, torque: 0 }],
            plies: [
              { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 0, thickness: 0.125 },
              { material_id: 'T300_5208', angle: -45, thickness: 0.125 },
              { material_id: 'T300_5208', angle: 45, thickness: 0.125 }
            ]
          });
        } else if (templateName === 'DUAL_HOLE') {
          set({
            width: 250,
            height: 120,
            holes: [
              { x: 70, y: 60, diameter: 6.35, load_magnitude: 3500, load_angle: 0, torque: 0 },
              { x: 170, y: 60, diameter: 6.35, load_magnitude: 3500, load_angle: 0, torque: 0 }
            ],
            plies: DEFAULT_PLIES
          });
        }
      },

      getValidationErrors: () => {
        const state = get();
        const errors: string[] = [];
        if (state.plies.length === 0) {
          errors.push("Katman dizilimi boş olamaz. En az 1 katman ekleyin.");
        }
        if (state.holes.length === 0) {
          errors.push("En az 1 delik tanımlanmalıdır.");
        }
        state.holes.forEach((h, idx) => {
          const r = h.diameter / 2.0;
          if (h.x - r < 0 || h.x + r > state.width || h.y - r < 0 || h.y + r > state.height) {
            errors.push(`Delik #${idx + 1} plaka sınırlarının dışına taşıyor! (X: ${h.x}, Y: ${h.y}, D: ${h.diameter})`);
          }
          // e/D edge distance check
          const e = Math.min(h.x, state.width - h.x, h.y, state.height - h.y);
          if (e / h.diameter < 1.5) {
            errors.push(`Delik #${idx + 1} için e/D kenar mesafesi oranı (${(e/h.diameter).toFixed(2)}) 1.5 kuralının altında!`);
          }
        });
        return errors;
      },

      resetToDefaults: () => set({
        plies: DEFAULT_PLIES,
        width: 200,
        height: 100,
        holes: DEFAULT_HOLES,
        constraintType: 'fixed',
        meshGlobal: 4.0,
        meshHole: 0.5,
        enablePDM: false,
        failureCriterion: 'Hashin',
        bypassLoad: 0,
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
        bypassLoad: state.bypassLoad,
        analysisHistory: state.analysisHistory,
      }),
    }
  )
);
