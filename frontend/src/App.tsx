import React, { useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { Header } from './components/Header';
import { PlyStacker } from './components/PlyStacker/PlyStacker';
import { GeometryEditor } from './components/GeometryEditor/GeometryEditor';
import { ContourPlot } from './components/StressViewer/ContourPlot';
import { ResultsSummary } from './components/ResultsPanel/ResultsSummary';
import { FailureTable } from './components/ResultsPanel/FailureTable';
import { MaterialManagerModal } from './components/MaterialManager/MaterialManagerModal';
import { CadStudioModal } from './components/CadStudio/CadStudioModal';
import { fetchMaterials, runAnalysis, downloadPdfReport } from './api/analysisApi';
import { useAnalysisStore } from './store/useAnalysisStore';
import { Activity, AlertCircle, Flame, RotateCcw } from 'lucide-react';

export const App: React.FC = () => {
  const {
    materials, setMaterials,
    isMaterialModalOpen, setIsMaterialModalOpen,
    isCadModalOpen, setIsCadModalOpen,
    plies, setPlies,
    width, setWidth,
    height, setHeight,
    holes, setHoles,
    constraintType, setConstraintType,
    meshGlobal, setMeshGlobal,
    meshHole, setMeshHole,
    enablePDM, setEnablePDM,
    failureCriterion, setFailureCriterion,
    results, setResults,
    loading, setLoading,
    error, setError,
    stressComponent, setStressComponent,
    applyCadData, resetToDefaults
  } = useAnalysisStore();

  const loadMaterialList = () => {
    fetchMaterials().then(setMaterials).catch(() => {
      toast.error('Malzeme veritabanı yüklenemedi!');
    });
  };

  useEffect(() => {
    loadMaterialList();
  }, []);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    const toastId = toast.loading('Sonlu Elemanlar (FEM) ve Hashin Matrisi Hesaplanıyor...');
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
      toast.success(`Analiz Başarıyla Tamamlandı! (Eleman Sayısı: ${res.elements.length})`, { id: toastId });
    } catch (err: any) {
      const msg = err.message || 'Analiz sırasında beklenmeyen bir hata oluştu';
      setError(msg);
      toast.error(msg, { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    const toastId = toast.loading('Sertifikasyon Raporu (PDF) Üretiliyor...');
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
      toast.success('Rapor İndirildi!', { id: toastId });
    } catch (err: any) {
      toast.error(`PDF İndirilemedi: ${err.message}`, { id: toastId });
    }
  };

  return (
    <div className="app-container">
      <Toaster position="top-right" toastOptions={{ duration: 4000, style: { background: '#0f172a', color: '#f8fafc', border: '1px solid #334155' } }} />

      <Header
        onRunAnalysis={handleRunAnalysis}
        loading={loading}
        onOpenMaterialManager={() => setIsMaterialModalOpen(true)}
        onOpenCadStudio={() => setIsCadModalOpen(true)}
        onExportPdf={handleExportPdf}
      />

      <MaterialManagerModal
        isOpen={isMaterialModalOpen}
        onClose={() => setIsMaterialModalOpen(false)}
        materials={materials}
        onRefreshMaterials={loadMaterialList}
      />

      <CadStudioModal
        isOpen={isCadModalOpen}
        onClose={() => setIsCadModalOpen(false)}
        onApplyToMainSolver={(params) => {
          applyCadData(params);
          toast.success(`CAD Verileri Aktarıldı: ${params.width || '?'}x${params.height || '?'} mm, ${params.holes.length} delik, ${params.plies?.length || 0} katman.`);
        }}
      />

      <main className="dashboard-content">
        {/* 3-Column Engineering Layout */}
        <div className="workstation-layout">
          
          {/* LEFT PANEL: Inputs */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingRight: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '-8px' }}>
              <button 
                className="btn btn-secondary" 
                style={{ fontSize: '0.75rem', padding: '4px 10px', color: 'var(--text-muted)' }}
                onClick={() => {
                  if (window.confirm('Tüm analizi varsayılan ayarlara sıfırlamak istediğinize emin misiniz?')) {
                    resetToDefaults();
                    toast.success('Analiz ayarları sıfırlandı.');
                  }
                }}
              >
                <RotateCcw size={12} style={{ marginRight: '4px' }} /> Analizi Sıfırla
              </button>
            </div>
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
            <button
              className="btn btn-primary"
              style={{ padding: '12px 16px', fontSize: '1rem', fontWeight: 700, borderRadius: '8px', width: '100%', flexShrink: 0, marginTop: 'auto' }}
              onClick={handleRunAnalysis}
              disabled={loading}
            >
              {loading ? '⚡ Çözülüyor...' : '▶ ANALİZİ ÇALIŞTIR'}
            </button>
            {error && (
              <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', padding: '12px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem' }}>
                <AlertCircle size={18} /><span>{error}</span>
              </div>
            )}
          </div>

          {/* CENTER PANEL: Viewport (Always visible) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', overflow: 'hidden' }}>
            {/* Gerilme Kontrol Barı */}
            <div className="glass-panel" style={{ padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', flexShrink: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <Activity size={18} /> <b>FEM Gerilme Dağılımı</b>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button className={`btn ${stressComponent === 'hashin_fi' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '4px 10px', fontSize: '0.75rem', background: stressComponent === 'hashin_fi' ? '#0ea5e9' : undefined }} onClick={() => setStressComponent('hashin_fi')}>🔥 Hashin FI</button>
                <button className={`btn ${stressComponent === 'von_mises' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => setStressComponent('von_mises')}>Von Mises</button>
                <button className={`btn ${stressComponent === 'sigma_x' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => setStressComponent('sigma_x')}>σx</button>
                <button className={`btn ${stressComponent === 'sigma_y' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => setStressComponent('sigma_y')}>σy</button>
                <button className={`btn ${stressComponent === 'tau_xy' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => setStressComponent('tau_xy')}>τxy</button>
              </div>
            </div>

            {/* Contour Plot Visualizer */}
            <div style={{ flex: 1, minHeight: 0, background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <ContourPlot
                nodes={results?.nodes || [[0, 0], [width, 0], [width, height], [0, height]]}
                elements={results?.elements || [[0, 1, 2, 3]]}
                stresses={results?.nodal_stresses}
                stressFrames={results?.stress_frames}
                nodalHashinFi={results?.nodal_hashin_fi}
                width={width}
                height={height}
                holes={holes}
                selectedComponent={stressComponent}
              />
            </div>
            
            {/* PDM Result Summary Badge */}
            {results?.pdm_results && (
              <div className="glass-panel" style={{ padding: '12px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#f0f9ff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: '8px', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Flame size={20} style={{ color: '#f59e0b' }} />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>İleri Düzey Kopma Analizi (PDM)</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>FPF Yükü: <b>{results.pdm_results.first_ply_failure_load_N.toFixed(0)} N</b> | Nihai Göçme: <b>{results.pdm_results.ultimate_load_N.toFixed(0)} N</b></div>
                  </div>
                </div>
                <div style={{ fontWeight: 700, padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', background: results.pdm_results.is_ultimate_failed ? 'rgba(239, 68, 68, 0.25)' : 'rgba(34, 197, 94, 0.25)', color: results.pdm_results.is_ultimate_failed ? '#f87171' : '#4ade80' }}>
                  {results.pdm_results.is_ultimate_failed ? 'ULTIMATE FAIL' : 'PASS'}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT PANEL: Results & Properties */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingLeft: '8px' }}>
            {results ? (
              <>
                <ResultsSummary results={results} />
                <FailureTable plyResults={results.ply_results} criticalPlyIndex={results.critical_ply} />
              </>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <Activity size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
                  <p style={{ fontSize: '0.9rem' }}>Analiz sonuçları burada görüntülenecektir.</p>
                </div>
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  );
};
