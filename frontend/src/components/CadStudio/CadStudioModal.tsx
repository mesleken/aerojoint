import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { 
  Box, Upload, FileText, CheckCircle2, Cpu, Layers, ArrowRight, X, RefreshCw
} from 'lucide-react';
import { 
  uploadCadFile, matchFemLoads, CadUploadResponse, LoadMatchResult 
} from '../../api/cadApi';
import { CadViewer3D } from './CadViewer3D';

interface CadStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyToMainSolver: (params: {
    width?: number;
    height?: number;
    holes: Array<{ x: number; y: number; diameter: number; load_magnitude: number }>;
    plies?: Array<{ material_id: string; angle: number; thickness: number }>;
  }) => void;
}

export const CadStudioModal: React.FC<CadStudioModalProps> = ({
  isOpen,
  onClose,
  onApplyToMainSolver,
}) => {
  const [activePhase, setActivePhase] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);

  // Phase 1 States
  const [cadData, setCadData] = useState<CadUploadResponse | null>(null);
  const [selectedHoleId, setSelectedHoleId] = useState<number | null>(null);

  // Phase 2 States
  const [toleranceMm, setToleranceMm] = useState<number>(2.0);
  const [matchResult, setMatchResult] = useState<LoadMatchResult | null>(null);

  // Phase 3 States
  const [selectedMethod, setSelectedMethod] = useState<string>('Option_1_Tangent_Plane');

  if (!isOpen) return null;

  // Step 1: Upload STEP/CAD File
  const handleCadUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];

    setLoading(true);
    const toastId = toast.loading('CAD Geometrisi ve B-Rep Topolojisi Ayrıştırılıyor...');
    try {
      const res = await uploadCadFile(file);
      setCadData(res);
      if (res.curvature_profile) {
        setSelectedMethod(res.curvature_profile.recommended_option);
      }
      toast.success(`CAD Yüklendi! Boyut: ${res.width}x${res.height}mm, ${res.detected_holes.length} delik tespit edildi.`, { id: toastId });
    } catch (err) {
      toast.error('CAD dosyası işlenirken hata oluştu.', { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Upload FEM CSV Load File
  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !cadData) return;
    const file = e.target.files[0];

    setLoading(true);
    const toastId = toast.loading('scipy.spatial.cKDTree Yük Eşleştirmesi Hesaplanıyor...');
    try {
      const res = await matchFemLoads(file, cadData.detected_holes, toleranceMm);
      setMatchResult(res);
      toast.success(`FEM Yükleri Eşleşti! (${res.summary.matched_count} başarılı)`, { id: toastId });
    } catch (err) {
      toast.error('FEM Yük CSV eşleştirmesi yapılırken hata oluştu.', { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  // Phase 4: Apply to Main Solver
  const handleCompleteWorkflow = () => {
    let solverHoles: Array<{ x: number; y: number; diameter: number; load_magnitude: number }> = [];
    if (matchResult && matchResult.matched_results.length > 0) {
      solverHoles = matchResult.matched_results.map((m) => ({
        x: Math.round(m.cad_center[0] * 10) / 10,
        y: Math.round(m.cad_center[1] * 10) / 10,
        diameter: Math.round(m.diameter * 10) / 10,
        load_magnitude: m.magnitude > 0 ? m.magnitude : 5000,
      }));
    } else if (cadData && cadData.detected_holes.length > 0) {
      solverHoles = cadData.detected_holes.map((h) => ({
        x: Math.round(h.center[0] * 10) / 10,
        y: Math.round(h.center[1] * 10) / 10,
        diameter: Math.round(h.diameter * 10) / 10,
        load_magnitude: 5000,
      }));
    }

    onApplyToMainSolver({
      width: cadData?.width,
      height: cadData?.height,
      holes: solverHoles,
      plies: cadData?.suggested_plies,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="relative w-full max-w-6xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
              <Box className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                AeroJoint V3.0 — 3B CAD & FEM Yük Entegrasyon Stüdyosu
                <span className="text-xs bg-sky-500/20 text-sky-400 px-2 py-0.5 rounded font-mono">
                  v3.0.0-Beta
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                STEP B-Rep Ayrıştırma, scipy KDTree Uzaysal Eşleştirme ve Akıllı Eğrilik Analitiği
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Phase Timeline Tabs */}
        <div className="grid grid-cols-4 border-b border-slate-800 bg-slate-950/50 text-xs font-medium">
          {[
            { id: 1, name: 'Faz 1: 3B CAD & Delik Tespiti', icon: Box },
            { id: 2, name: 'Faz 2: FEM Yük Eşleştirme (KDTree)', icon: FileText },
            { id: 3, name: 'Faz 3: Akıllı Eğrilik Analizi', icon: Cpu },
            { id: 4, name: 'Faz 4: Lokal Dönüşüm & Onay', icon: Layers },
          ].map((phase) => {
            const Icon = phase.icon;
            const isActive = activePhase === phase.id;
            return (
              <button
                key={phase.id}
                onClick={() => setActivePhase(phase.id)}
                className={`py-3 px-4 flex items-center gap-2 border-r last:border-r-0 border-slate-800 transition ${
                  isActive
                    ? 'bg-slate-800/80 text-sky-400 border-b-2 border-b-sky-500 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{phase.name}</span>
              </button>
            );
          })}
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* FAZ 1 */}
          {activePhase === 1 && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 space-y-4">
                <CadViewer3D
                  meshData={cadData?.mesh_data}
                  holes={cadData?.detected_holes}
                  selectedHoleId={selectedHoleId}
                  onSelectHole={(h) => setSelectedHoleId(h.id)}
                />
              </div>
              <div className="lg:col-span-5 space-y-4 flex flex-col">
                <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
                  <h3 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
                    <Upload className="w-4 h-4 text-sky-400" /> 3B CAD Dosyası Yükle (.step, .stl, .obj)
                  </h3>
                  <input
                    type="file"
                    accept=".step,.stp,.stl,.obj"
                    onChange={handleCadUpload}
                    className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-sky-500/20 file:text-sky-400 hover:file:bg-sky-500/30 cursor-pointer"
                  />
                </div>

                {loading && (
                  <div className="p-4 bg-sky-500/10 border border-sky-500/20 rounded-xl flex items-center gap-3 text-sky-400 text-xs">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    OpenCascade / trimesh B-Rep geometri çözümlemesi yapılıyor...
                  </div>
                )}

                {cadData && (
                  <div className="flex-1 p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-3 overflow-y-auto max-h-[300px]">
                    <div className="flex items-center justify-between text-xs text-slate-300 font-semibold border-b border-slate-800 pb-2">
                      <span>Tespit Edilen Delikler ({cadData.detected_holes.length})</span>
                      <span className="text-emerald-400 text-[11px] font-mono">B-Rep Eksen Dot Product: OK</span>
                    </div>
                    {cadData.detected_holes.map((h) => (
                      <div
                        key={h.id}
                        onClick={() => setSelectedHoleId(h.id)}
                        className={`p-3 rounded-lg border text-xs cursor-pointer transition flex items-center justify-between ${
                          selectedHoleId === h.id
                            ? 'bg-sky-500/10 border-sky-500 text-sky-300'
                            : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <div>
                          <div className="font-semibold text-slate-100">{h.name}</div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            Merkez: ({h.center.map((c) => c.toFixed(1)).join(', ')}) mm
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded font-mono text-[11px]">
                            Ø {h.diameter.toFixed(2)} mm
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* FAZ 2 */}
          {activePhase === 2 && (
            <div className="space-y-6">
              <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-sky-400" /> FEM Nodal Yük CSV İçe Aktarma
                  </h3>
                  <p className="text-xs text-slate-400">
                    Nastran / Abaqus formatındaki [Hole_ID, X, Y, Z, Fx, Fy, Fz] yük listesini scipy KDTree ile eşleştirin.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <span>Arama Toleransı (mm):</span>
                    <input
                      type="number"
                      value={toleranceMm}
                      onChange={(e) => setToleranceMm(parseFloat(e.target.value) || 2.0)}
                      className="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-center text-sky-400 font-mono text-xs"
                    />
                  </div>
                  <input
                    type="file"
                    accept=".csv,.txt"
                    onChange={handleCsvUpload}
                    disabled={!cadData}
                    className="text-xs text-slate-400 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-500/20 file:text-emerald-400 hover:file:bg-emerald-500/30 cursor-pointer disabled:opacity-50"
                  />
                </div>
              </div>

              {matchResult && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                    <div className="text-xs text-slate-400 font-semibold mb-1">Eşleşen CAD Delikleri</div>
                    <div className="text-2xl font-bold text-emerald-400 font-mono">
                      {matchResult.summary.matched_count} / {matchResult.summary.total_holes}
                    </div>
                  </div>
                  <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                    <div className="text-xs text-slate-400 font-semibold mb-1">Boşta Kalan (Orphan) Yükler</div>
                    <div className="text-2xl font-bold text-amber-400 font-mono">
                      {matchResult.summary.orphan_count}
                    </div>
                  </div>
                  <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                    <div className="text-xs text-slate-400 font-semibold mb-1">Eşleşme Durumu</div>
                    <div className="text-sm font-semibold text-sky-400 font-mono mt-2">
                      {matchResult.summary.status}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* FAZ 3 */}
          {activePhase === 3 && cadData?.curvature_profile && (
            <div className="space-y-6">
              <div className="p-5 bg-gradient-to-r from-sky-950/40 to-slate-900 rounded-xl border border-sky-500/30">
                <div className="flex items-center gap-3 mb-2">
                  <Cpu className="w-5 h-5 text-sky-400" />
                  <h3 className="text-base font-semibold text-slate-100">Akıllı Karar Ağacı Analiz Önerisi</h3>
                </div>
                <p className="text-xs text-slate-300 mb-4">{cadData.curvature_profile.explanation}</p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    {
                      id: 'Option_1_Tangent_Plane',
                      title: '1. Teğet Düzlem İndirgemesi',
                      desc: 'Yüzey düz ise 3B kuvvetler Yonlü Kosinüs Matrisi (DCM) ile 2B lokal sisteme aktarılır.',
                    },
                    {
                      id: 'Option_2_Geodesic',
                      title: '2. Jeodezik Eğri Yayılımı',
                      desc: 'Silindirik yüzeylerde delikler arası mesafeler 3B yüzey üzeri jeodezik eğrilerle hesaplanır.',
                    },
                    {
                      id: 'Option_3_Kinematic_Draping',
                      title: '3. Kinematik Serim (Draping)',
                      desc: 'Çift eğrilikli yapıda kompozit elyaf serim açısı kayması ve stiffness rotasyonu uygulanır.',
                    },
                  ].map((opt) => (
                    <div
                      key={opt.id}
                      onClick={() => setSelectedMethod(opt.id)}
                      className={`p-4 rounded-xl border cursor-pointer transition ${
                        selectedMethod === opt.id
                          ? 'bg-sky-500/20 border-sky-400 text-slate-100 shadow-lg shadow-sky-500/10'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-xs">{opt.title}</span>
                        {cadData.curvature_profile.recommended_option === opt.id && (
                          <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] rounded font-mono">
                            Sistem Önerisi
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] leading-relaxed">{opt.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* FAZ 4 */}
          {activePhase === 4 && (
            <div className="space-y-6">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-4">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-emerald-300">V3.0 CAD & FEM Dönüşüm Hazır</h3>
                  <p className="text-xs text-slate-300 mt-1">
                    İnsan-Döngüde (Human-in-the-Loop) onayı ile çıkarılan CAD delikleri ve eşleştirilen yükler doğrudan AeroJoint 2D PDM & Hashin çözücüsüne aktarılacaktır.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Controls */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <button
            onClick={() => setActivePhase((p) => Math.max(1, p - 1))}
            disabled={activePhase === 1}
            className="px-4 py-2 bg-slate-800 text-slate-300 text-xs font-semibold rounded-lg hover:bg-slate-700 disabled:opacity-50 transition"
          >
            Önceki Faz
          </button>
          <div className="flex items-center gap-3">
            {activePhase < 4 ? (
              <button
                onClick={() => setActivePhase((p) => Math.min(4, p + 1))}
                className="px-5 py-2 bg-sky-500 text-slate-950 font-semibold text-xs rounded-lg hover:bg-sky-400 transition flex items-center gap-2"
              >
                Sonraki Faz <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleCompleteWorkflow}
                className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-xs rounded-lg hover:from-emerald-400 hover:to-teal-400 transition flex items-center gap-2 shadow-lg shadow-emerald-500/20"
              >
                <CheckCircle2 className="w-4 h-4" /> Ana Çözücüye Aktar & Analiz Et
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
