import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PlyStacker } from './components/PlyStacker/PlyStacker';
import { GeometryEditor } from './components/GeometryEditor/GeometryEditor';
import { ContourPlot } from './components/StressViewer/ContourPlot';
import { ResultsSummary } from './components/ResultsPanel/ResultsSummary';
import { FailureTable } from './components/ResultsPanel/FailureTable';
import { MaterialManagerModal } from './components/MaterialManager/MaterialManagerModal';
import { PlyInput, HoleInput, AnalysisResponse, MaterialOption } from './types/analysis';
import { fetchMaterials, runAnalysis, downloadPdfReport } from './api/analysisApi';
import { Activity, AlertCircle, Play, ShieldCheck, Flame } from 'lucide-react';

export const App: React.FC = () => {
  const [materials, setMaterials] = useState<MaterialOption[]>([]);
  const [isMaterialModalOpen, setIsMaterialModalOpen] = useState<boolean>(false);

  const [plies, setPlies] = useState<PlyInput[]>([
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
  ]);

  const [width, setWidth] = useState<number>(200);
  const [height, setHeight] = useState<number>(100);
  
  const [holes, setHoles] = useState<HoleInput[]>([
    { x: 60, y: 50, diameter: 6.35, load_magnitude: 1500, load_angle: 0, torque: 0 }
  ]);
  const [constraintType, setConstraintType] = useState<string>('fixed');
  const [meshGlobal, setMeshGlobal] = useState<number>(6.0);
  const [meshHole, setMeshHole] = useState<number>(1.2);
  const [enablePDM, setEnablePDM] = useState<boolean>(false);
  const [failureCriterion, setFailureCriterion] = useState<string>('Hashin');

  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [stressComponent, setStressComponent] = useState<'sigma_x' | 'sigma_y' | 'tau_xy' | 'von_mises'>('von_mises');

  const loadMaterialList = () => {
    fetchMaterials().then(setMaterials);
  };

  useEffect(() => {
    loadMaterialList();
  }, []);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runAnalysis({
        width,
        height,
        plies,
        holes,
        constraint_type: constraintType,
        mesh_size_global: meshGlobal,
        mesh_size_hole: meshHole,
        enable_pdm: enablePDM,
        failure_criterion: failureCriterion as any
      });
      setResults(res);
    } catch (err: any) {
      setError(err.message || 'Analiz sırasında beklenmeyen bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    try {
      const blob = await downloadPdfReport({
        width, height, plies, holes, constraint_type: constraintType,
        mesh_size_global: meshGlobal, mesh_size_hole: meshHole,
        enable_pdm: enablePDM, failure_criterion: failureCriterion as any
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AeroJoint_Report_${Date.now()}.${blob.type.includes('pdf') ? 'pdf' : 'html'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`PDF İndirilemedi: ${err.message}`);
    }
  };

  return (
    <div className="app-container">
      <Header
        onRunAnalysis={handleRunAnalysis}
        loading={loading}
        onOpenMaterialManager={() => setIsMaterialModalOpen(true)}
        onExportPdf={handleExportPdf}
      />

      <MaterialManagerModal
        isOpen={isMaterialModalOpen}
        onClose={() => setIsMaterialModalOpen(false)}
        materials={materials}
        onRefreshMaterials={loadMaterialList}
      />

      <main className="dashboard-content">
        <section>
          <div className="input-grid">
            <PlyStacker
              plies={plies}
              materials={materials}
              onChange={setPlies}
            />

            <GeometryEditor
              width={width}
              height={height}
              holes={holes}
              constraintType={constraintType}
              meshGlobal={meshGlobal}
              meshHole={meshHole}
              enablePDM={enablePDM}
              failureCriterion={failureCriterion}
              onChangeWidth={setWidth}
              onChangeHeight={setHeight}
              onChangeHoles={setHoles}
              onChangeConstraint={setConstraintType}
              onChangeMeshGlobal={setMeshGlobal}
              onChangeMeshHole={setMeshHole}
              onChangePDM={setEnablePDM}
              onChangeCriterion={setFailureCriterion}
            />
          </div>
        </section>

        <section className="action-bar">
          <button
            className="btn btn-primary"
            style={{ padding: '12px 36px', fontSize: '1rem', fontWeight: 700, borderRadius: '8px' }}
            onClick={handleRunAnalysis}
            disabled={loading}
          >
            {loading ? (
              '⚡ Sonlu Elemanlar (FEM) & Progressive Damage Çözülüyor...'
            ) : (
              <>
                <Play size={20} style={{ fill: 'currentColor' }} /> ▶ ANALİZİ ÇALIŞTIR VE SERTİFİKASYON RAPORU ÜRET
              </>
            )}
          </button>
        </section>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171', padding: '12px 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <section className="results-section">
          {/* PDM Result Summary Badge */}
          {results?.pdm_results && (
            <div className="glass-panel" style={{ padding: '12px 18px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#f0f9ff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Flame size={22} style={{ color: '#f59e0b' }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>İleri Düzey Kopma Analizi (Progressive Damage Modeling)</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    İlk Katman Hasar Yükü (FPF): <b>{results.pdm_results.first_ply_failure_load_N.toFixed(0)} N</b> | Nihai Yapısal Göçme Yükü (Ultimate Load): <b>{results.pdm_results.ultimate_load_N.toFixed(0)} N</b>
                  </div>
                </div>
              </div>
              <div style={{ fontWeight: 700, padding: '4px 12px', borderRadius: '6px', fontSize: '0.85rem', background: results.pdm_results.is_ultimate_failed ? 'rgba(239, 68, 68, 0.25)' : 'rgba(34, 197, 94, 0.25)', color: results.pdm_results.is_ultimate_failed ? '#f87171' : '#4ade80' }}>
                {results.pdm_results.is_ultimate_failed ? 'NİHAİ KOPMA GERÇEKLEŞTİ (ULTIMATE FAIL)' : 'NİHAİ TAŞIMA KAPASİTESİ UYGUN (PASS)'}
              </div>
            </div>
          )}

          {/* Gerilme Kontrol Barı */}
          <div className="glass-panel" style={{ padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              <Activity size={18} /> <b>Sonlu Elemanlar (FEM) Gerilme Dağılım Haritası</b>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className={`btn ${stressComponent === 'von_mises' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                onClick={() => setStressComponent('von_mises')}
              >
                Von Mises
              </button>
              <button
                className={`btn ${stressComponent === 'sigma_x' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                onClick={() => setStressComponent('sigma_x')}
              >
                σx
              </button>
              <button
                className={`btn ${stressComponent === 'sigma_y' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                onClick={() => setStressComponent('sigma_y')}
              >
                σy
              </button>
              <button
                className={`btn ${stressComponent === 'tau_xy' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                onClick={() => setStressComponent('tau_xy')}
              >
                τxy
              </button>
            </div>
          </div>

          {/* Contour Plot Visualizer */}
          <ContourPlot
            nodes={results?.nodes || [[0, 0], [width, 0], [width, height], [0, height]]}
            elements={results?.elements || [[0, 1, 2, 3]]}
            stresses={results?.nodal_stresses}
            stressFrames={results?.stress_frames}
            width={width}
            height={height}
            holes={holes}
            selectedComponent={stressComponent}
          />

          {/* Analiz Sonuç Panelleri */}
          {results && (
            <>
              <ResultsSummary results={results} />
              <FailureTable plyResults={results.ply_results} criticalPlyIndex={results.critical_ply} />
            </>
          )}
        </section>
      </main>
    </div>
  );
};
