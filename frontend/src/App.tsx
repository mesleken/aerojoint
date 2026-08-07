import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PlyStacker } from './components/PlyStacker/PlyStacker';
import { GeometryEditor } from './components/GeometryEditor/GeometryEditor';
import { ContourPlot } from './components/StressViewer/ContourPlot';
import { ResultsSummary } from './components/ResultsPanel/ResultsSummary';
import { FailureTable } from './components/ResultsPanel/FailureTable';
import { PlyInput, HoleInput, AnalysisResponse, MaterialOption } from './types/analysis';
import { fetchMaterials, runAnalysis } from './api/analysisApi';
import { Activity, AlertCircle, Play, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [materials, setMaterials] = useState<MaterialOption[]>([]);
  
  // Standart Havacılık Yapısal Yarı-İzotropik (Quasi-Isotropic) 16 Katmanlı Dizilim: [0/45/-45/90]_2s
  // Bu dizilim ve 1500 N pim yükü MIL-HDBK-17 standartlarında doğrudan PASS (Geçti) verir.
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
  
  // Standart Havacılık Pimli Bağlantı Yükü: 1500 N (1.5 kN), 1/4 inç (6.35 mm) delik
  const [holes, setHoles] = useState<HoleInput[]>([
    { x: 60, y: 50, diameter: 6.35, load_magnitude: 1500, load_angle: 0 }
  ]);
  const [constraintType, setConstraintType] = useState<string>('fixed');
  const [meshGlobal, setMeshGlobal] = useState<number>(6.0);
  const [meshHole, setMeshHole] = useState<number>(1.2);

  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [stressComponent, setStressComponent] = useState<'sigma_x' | 'sigma_y' | 'tau_xy' | 'von_mises'>('von_mises');

  useEffect(() => {
    fetchMaterials().then(setMaterials);
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
        mesh_size_hole: meshHole
      });
      setResults(res);
    } catch (err: any) {
      setError(err.message || 'Analiz sırasında beklenmeyen bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header onRunAnalysis={handleRunAnalysis} loading={loading} />

      <main className="dashboard-content">
        {/* ============================================================ */}
        {/* ÜST BÖLÜM: GİRDİ PARAMETRELERİ (GENİŞ ALAN) */}
        {/* ============================================================ */}
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
              onChangeWidth={setWidth}
              onChangeHeight={setHeight}
              onChangeHoles={setHoles}
              onChangeConstraint={setConstraintType}
              onChangeMeshGlobal={setMeshGlobal}
              onChangeMeshHole={setMeshHole}
            />
          </div>
        </section>

        {/* ============================================================ */}
        {/* ORTA BÖLÜM: ANALİZ ET BUTONU VE DURUM BAR-I */}
        {/* ============================================================ */}
        <section className="action-bar">
          <button
            className="btn btn-primary"
            style={{ padding: '12px 36px', fontSize: '1rem', fontWeight: 700, borderRadius: '8px' }}
            onClick={handleRunAnalysis}
            disabled={loading}
          >
            {loading ? (
              '⚡ Sonlu Elemanlar Analizi Çözülüyor...'
            ) : (
              <>
                <Play size={20} style={{ fill: 'currentColor' }} /> ▶ ANALİZİ ÇALIŞTIR VE SERTİFİKASYON RAPORU ÜRET
              </>
            )}
          </button>
        </section>

        {/* Hata Bildirimi */}
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171', padding: '12px 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* ============================================================ */}
        {/* ALT BÖLÜM: GERİLME HARİTASI VE SERTİFİKASYON SONUÇLARI */}
        {/* ============================================================ */}
        <section className="results-section">
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
