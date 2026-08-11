import React, { useMemo, useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Maximize2, Target, Crosshair } from 'lucide-react';

interface Props {
  nodes: number[][];
  elements: number[][];
  stresses?: number[][]; // [N_nodes, 3] (sigma_x, sigma_y, tau_xy)
  stressFrames?: number[][][]; // Multi-step PDM frames
  width: number;
  height: number;
  selectedComponent?: 'sigma_x' | 'sigma_y' | 'tau_xy' | 'von_mises' | 'hashin_fi';
  holes?: Array<{ x: number; y: number; diameter: number }>;
  nodalHashinFi?: number[];
}

// Mühendislik CAD Standartlarında Dinamik "Nice Step" Adım Hesaplama Algoritması
function getNiceStep(span: number, targetCount: number = 5): number {
  if (span <= 0) return 10;
  const rawStep = span / targetCount;
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const frac = rawStep / mag;
  let niceMult = 1;
  if (frac >= 1.5 && frac < 3.5) niceMult = 2;
  else if (frac >= 3.5 && frac < 7.5) niceMult = 5;
  else if (frac >= 7.5) niceMult = 10;
  return Math.max(1, niceMult * mag);
}

export const ContourPlot: React.FC<Props> = ({
  nodes,
  elements,
  stresses,
  stressFrames,
  width,
  height,
  selectedComponent = 'von_mises',
  holes = [],
  nodalHashinFi
}) => {
  const [viewMode, setViewMode] = useState<'fit' | 'critical'>('critical');
  const [showMesh, setShowMesh] = useState<boolean>(false);
  const [activeFrameIndex, setActiveFrameIndex] = useState<number>(0);

  const activeStresses = useMemo(() => {
    if (stressFrames && stressFrames.length > 0 && stressFrames[activeFrameIndex]) {
      return stressFrames[activeFrameIndex];
    }
    return stresses;
  }, [stresses, stressFrames, activeFrameIndex]);

  const intensity = useMemo(() => {
    if (selectedComponent === 'hashin_fi') {
      if (nodalHashinFi && nodalHashinFi.length === nodes.length) {
        return nodalHashinFi;
      }
      return new Array(nodes.length).fill(0);
    }

    if (!activeStresses || activeStresses.length === 0) {
      return new Array(nodes.length).fill(0);
    }

    return activeStresses.map(s => {
      const [sx, sy, txy] = s;
      if (selectedComponent === 'sigma_x') return sx;
      if (selectedComponent === 'sigma_y') return sy;
      if (selectedComponent === 'tau_xy') return txy;
      return Math.sqrt(Math.max(0, sx * sx - sx * sy + sy * sy + 3 * txy * txy));
    });
  }, [activeStresses, nodes.length, selectedComponent, nodalHashinFi]);

  // En yüksek gerilmeye sahip kritik düğümü bul (Stress Concentration Peak)
  const criticalPoint = useMemo(() => {
    if (!activeStresses || activeStresses.length === 0 || nodes.length === 0) {
      return { x: width / 2, y: height / 2, stress: 0 };
    }
    let maxVal = -1;
    let maxIdx = 0;
    intensity.forEach((val, idx) => {
      if (val > maxVal) {
        maxVal = val;
        maxIdx = idx;
      }
    });
    return {
      x: nodes[maxIdx][0],
      y: nodes[maxIdx][1],
      stress: maxVal
    };
  }, [activeStresses, intensity, nodes, width, height]);

  useEffect(() => {
    if (stresses && stresses.length > 0) {
      setViewMode('critical');
    }
  }, [stresses]);

  const x = useMemo(() => nodes.map(n => n[0]), [nodes]);
  const y = useMemo(() => nodes.map(n => n[1]), [nodes]);

  const { i, j, k } = useMemo(() => {
    const iArr: number[] = [];
    const jArr: number[] = [];
    const kArr: number[] = [];

    elements.forEach(elem => {
      if (elem.length === 4) {
        iArr.push(elem[0], elem[0]);
        jArr.push(elem[1], elem[2]);
        kArr.push(elem[2], elem[3]);
      } else if (elem.length === 3) {
        iArr.push(elem[0]);
        jArr.push(elem[1]);
        kArr.push(elem[2]);
      }
    });

    return { i: iArr, j: jArr, k: kArr };
  }, [elements]);

  // FEM Mesh Wireframe Edge Traces (Canlı FEM Mesh Görüntüleyici)
  const meshWireframeTrace = useMemo(() => {
    if (!showMesh || !elements || elements.length === 0) return null;

    const edgeX: (number | null)[] = [];
    const edgeY: (number | null)[] = [];
    const edgeZ: (number | null)[] = [];

    elements.forEach(elem => {
      const len = elem.length;
      for (let idx = 0; idx < len; idx++) {
        const n1 = nodes[elem[idx]];
        const n2 = nodes[elem[(idx + 1) % len]];
        if (n1 && n2) {
          edgeX.push(n1[0], n2[0], null);
          edgeY.push(n1[1], n2[1], null);
          edgeZ.push(0.01, 0.01, null);
        }
      }
    });

    return {
      type: 'scatter3d',
      mode: 'lines',
      x: edgeX,
      y: edgeY,
      z: edgeZ,
      line: { color: 'rgba(255, 255, 255, 0.25)', width: 1 },
      hoverinfo: 'none',
      showlegend: false
    };
  }, [showMesh, elements, nodes]);

  // Plaka Dış Sınır Çizgisi (Cyan Boundary Wireframe)
  const plateBoundaryTrace = useMemo(() => {
    return {
      type: 'scatter3d',
      mode: 'lines',
      x: [0, width, width, 0, 0],
      y: [0, 0, height, height, 0],
      z: [0, 0, 0, 0, 0],
      line: { color: '#06b6d4', width: 3.5 },
      hoverinfo: 'none',
      showlegend: false
    };
  }, [width, height]);

  // Plaka Boyutuna Göre Dinamik Adaptif Kadraj Çarpanı
  const adaptiveScaleFactor = useMemo(() => {
    const maxDim = Math.max(width, height);
    if (maxDim <= 200) return 0.38;
    if (maxDim >= 1000) return 0.20;
    return 0.38 - (maxDim - 200) * (0.18 / 800);
  }, [width, height]);

  const minDim = Math.max(1, Math.min(width, height));
  const nticksX = useMemo(() => {
    if (viewMode === 'critical') return 12; // Kritik bölge zoom'unda sıkışmayı önlemek için az tick
    return Math.min(60, Math.max(20, Math.round(30 * (width / minDim))));
  }, [width, minDim, viewMode]);
  
  const nticksY = useMemo(() => {
    if (viewMode === 'critical') return 12;
    return Math.min(60, Math.max(20, Math.round(30 * (height / minDim))));
  }, [height, minDim, viewMode]);

  const criticalHoleTarget = useMemo(() => {
    if (!holes || holes.length === 0) {
      return { x: criticalPoint.x, y: criticalPoint.y, diameter: 10.0 };
    }
    let minDist = Infinity;
    let target = { x: holes[0].x, y: holes[0].y, diameter: holes[0].diameter };
    holes.forEach(h => {
      const dist = Math.hypot(h.x - criticalPoint.x, h.y - criticalPoint.y);
      if (dist < minDist) {
        minDist = dist;
        target = { x: h.x, y: h.y, diameter: h.diameter };
      }
    });
    return target;
  }, [holes, criticalPoint]);

   // Adaptif Kadraj Formülasyonlu Eksen & Kamera Yapılandırması
  const { xRange, yRange, cameraConfig, sceneAspectMode, sceneAspectRatio } = useMemo(() => {
    if (viewMode === 'critical' && activeStresses && activeStresses.length > 0) {
      const minDim = Math.min(width, height);
      
      // 1. Temel Odak: Deliğin etrafındaki gerilme yığılmasını tam görmek için çapın 2.5 katı
      const baseSpan = criticalHoleTarget.diameter * 2.5;
      
      // 2. Alt Sınır (Çok küçük delikler için): Bağlamı kaybetmemek adına plakanın kısa kenarının en az %20'si
      // (Örn: 200x100 plakada minDim=100 -> minSpan = 20. Sizin referansınızla birebir aynı!)
      const minSpan = minDim * 0.20;
      
      // 3. Üst Sınır (Çok büyük delikler için): Plaka dışındaki boşluğa (uzaya) zoom out yapmamak için
      // plakanın kısa kenarının yarısını (yani ekrana tam oturmasını) geçmesin
      const maxSpan = minDim * 0.50;
      
      // Formül: Temel odağı al, ancak alt ve üst sınırlar dışına taşıyorsa sınırla (clamp)
      const zoomSpan = Math.max(minSpan, Math.min(baseSpan, maxSpan));
      
      return {
        xRange: [criticalHoleTarget.x - zoomSpan, criticalHoleTarget.x + zoomSpan],
        yRange: [criticalHoleTarget.y - zoomSpan, criticalHoleTarget.y + zoomSpan],
        cameraConfig: {
          center: { x: 0, y: 0, z: 0 },
          eye: { x: 0, y: 0, z: 2.5 }
        },
        sceneAspectMode: 'manual',
        sceneAspectRatio: { 
          x: 1.5, 
          y: 1.5, 
          z: 0.05 
        }
      };
    }

    // Tüm Plakayı Sığdır (Sıfıra yakın eksen offset'i)
    const maxDim = Math.max(width, height);
    const minDim = Math.min(width, height);
    const ratio = maxDim / minDim;
    
    // Kullanıcının kalibrasyon verilerinden türetilen kesin matematiksel formül:
    // R=1.0 -> M=1.50, R=1.5 -> M=2.25 vb.
    // Doğrusal Denklem: M = 1.5 * Ratio
    let m = 1.5 * ratio;

    return {
      xRange: [-width * 0.01, width * 1.01],
      yRange: [-height * 0.01, height * 1.01],
      cameraConfig: {
        center: { x: 0, y: 0, z: 0 },
        eye: { x: 0, y: 0, z: 2.5 }
      },
      sceneAspectMode: 'manual',
      sceneAspectRatio: { 
        x: m * (width / maxDim), 
        y: m * (height / maxDim), 
        z: 0.05 
      }
    };
  }, [viewMode, criticalPoint, criticalHoleTarget, width, height, activeStresses, adaptiveScaleFactor]);

  const hoverTextList = useMemo(() => {
    return nodes.map((n, idx) => {
      const val = intensity[idx] || 0;
      return `📍 Konum: X = ${n[0].toFixed(1)} mm, Y = ${n[1].toFixed(1)} mm<br>⚡ Gerilme: ${val.toFixed(2)} MPa`;
    });
  }, [nodes, intensity]);

  const holeBoundaryTraces = useMemo(() => {
    // Beyaz halkalar (CAD çizimi) kaldırıldı
    return [];
  }, [holes]);

  const dataTraces: any[] = [
    {
      type: 'mesh3d',
      x,
      y,
      z: new Array(x.length).fill(0),
      i,
      j,
      k,
      intensity,
      colorscale: 'Jet',
      colorbar: {
        title: { text: selectedComponent === 'hashin_fi' ? 'HASHIN FI' : selectedComponent.toUpperCase() + ' (MPa)', font: { color: '#38bdf8', size: 12 }, side: 'top' },
        tickfont: { color: '#94a3b8', size: 11 },
        len: 0.85,
        x: 1.05,
        thickness: 16
      },
      flatshading: true,
      showscale: true,
      hoverinfo: 'text',
      text: hoverTextList
    },
    plateBoundaryTrace,
    ...holeBoundaryTraces
  ];

  if (meshWireframeTrace) {
    dataTraces.push(meshWireframeTrace);
  }

  const uiRevisionKey = `${viewMode}_${width}_${height}_${criticalPoint.x.toFixed(1)}_${criticalPoint.y.toFixed(1)}_${selectedComponent}_${holes.map(h => `${h.diameter}_${h.x}_${h.y}`).join(',')}`;
  // Kullanıcının isteği üzerine panel her zaman kare (1:1) kalacak.
  // Bu sayede yatay/dikey asimetrisi ortadan kalkıyor ve tek formül kusursuz çalışıyor.
  const viewportAspect = 1.0;

  return (
    <div className="glass-panel" style={{ padding: '14px', flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Üst Kontrol & Eksen Bilgi Barı */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <span>📏 Plaka Boyutu: <b>{width} × {height} mm</b></span>
          {activeStresses && activeStresses.length > 0 && (
            <span style={{ color: 'var(--accent-amber)', background: 'rgba(245, 158, 11, 0.15)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
              <Crosshair size={12} style={{ display: 'inline', marginRight: '4px' }} />
              Max Gerilme Odağı: X = {criticalPoint.x.toFixed(1)} mm | Y = {criticalPoint.y.toFixed(1)} mm ({criticalPoint.stress.toFixed(1)} MPa)
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {/* FEM Mesh Wireframe Toggle */}
          <button
            className={`btn ${showMesh ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '3px 8px', fontSize: '0.75rem' }}
            onClick={() => setShowMesh(!showMesh)}
            title="FEM Eleman Ağını Göster/Gizle"
          >
            {showMesh ? '🕸️ Mesh Açık' : '🕸️ Mesh Kapalı'}
          </button>

          <button
            className={`btn ${viewMode === 'fit' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '3px 8px', fontSize: '0.75rem' }}
            onClick={() => setViewMode('fit')}
          >
            <Maximize2 size={13} /> Tüm Plakayı Sığdır
          </button>
          <button
            className={`btn ${viewMode === 'critical' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '3px 8px', fontSize: '0.75rem' }}
            onClick={() => setViewMode('critical')}
          >
            <Target size={13} /> Kritik Bölge Zoom
          </button>
        </div>
      </div>

      {/* Stress Animation Slider for PDM frames */}
      {stressFrames && stressFrames.length > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: '#1e293b', padding: '6px 12px', borderRadius: '6px', fontSize: '0.8rem' }}>
          <span style={{ color: '#38bdf8', fontWeight: 600 }}>🎬 Yükleme Adımı Animasyonu:</span>
          <input
            type="range"
            min={0}
            max={stressFrames.length - 1}
            value={activeFrameIndex}
            onChange={(e) => setActiveFrameIndex(parseInt(e.target.value))}
            style={{ flex: 1, cursor: 'pointer' }}
          />
          <span>Adım {activeFrameIndex + 1} / {stressFrames.length} (%{Math.round(((activeFrameIndex + 1) / stressFrames.length) * 100)} Yük)</span>
        </div>
      )}

      {/* Plotly Dinamik Adaptif Kadrajlı Görselleştirici */}
      <div style={{ width: '100%', maxWidth: '200vh', maxHeight: '100vh', aspectRatio: '1 / 1', display: 'flex', margin: '0 auto', background: 'rgba(0,0,0,0.15)', borderRadius: '8px' }}>
        <Plot
          data={dataTraces}
          layout={{
            uirevision: uiRevisionKey,
            autosize: true,
            margin: { l: 65, r: 85, t: 25, b: 70 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            showlegend: false,
            scene: {
              xaxis: {
                title: { text: 'X (mm)', font: { color: '#38bdf8', size: 12 } },
                color: '#94a3b8',
                range: xRange,
                showgrid: true,
                gridcolor: '#475569',
                nticks: nticksX,
                showticklabels: true,
                zeroline: true,
                zerolinecolor: '#06b6d4',
                zerolinewidth: 3,
                showbackground: false
              },
              yaxis: {
                title: { text: 'Y (mm)', font: { color: '#38bdf8', size: 12 } },
                color: '#94a3b8',
                range: yRange,
                showgrid: true,
                gridcolor: '#475569',
                nticks: nticksY,
                showticklabels: true,
                zeroline: true,
                zerolinecolor: '#06b6d4',
                zerolinewidth: 3,
                showbackground: false
              },
              zaxis: { visible: false },
              camera: {
                center: cameraConfig.center,
                eye: cameraConfig.eye,
                up: { x: 0, y: 1, z: 0 },
                // @ts-ignore
                projection: { type: 'orthographic' }
              },
              aspectmode: sceneAspectMode,
              ...(sceneAspectRatio && { aspectratio: sceneAspectRatio })
            }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
          config={{ responsive: true, displayModeBar: false }}
        />
      </div>
    </div>
  );
};
