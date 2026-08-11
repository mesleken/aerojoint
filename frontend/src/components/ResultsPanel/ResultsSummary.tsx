import React from 'react';
import { AnalysisResponse } from '../../types/analysis';
import { ShieldCheck, ShieldAlert, Cpu, Layers } from 'lucide-react';

interface Props {
  results: AnalysisResponse;
}

export const ResultsSummary: React.FC<Props> = ({ results }) => {
  const isPass = results.overall_status === 'PASS';
  const mos = results.min_mos;
  
  // Calculate gauge parameters
  // Max expected MoS for visual scaling could be around 2.0.
  // 0 or below is red. 0 to 0.5 is amber. > 0.5 is green.
  const cappedMos = Math.max(-1, Math.min(2, mos));
  const gaugePercent = ((cappedMos + 1) / 3) * 100; // -1 to 2 mapped to 0-100%
  let gaugeColor = 'var(--accent-green)';
  if (mos < 0) gaugeColor = 'var(--accent-red)';
  else if (mos < 0.5) gaugeColor = 'var(--accent-amber)';

  return (
    <div className="glass-panel" style={{ padding: '14px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', alignItems: 'center' }}>
        
        {/* Status Box */}
        <div style={{
          background: isPass ? 'rgba(63, 183, 127, 0.1)' : 'rgba(224, 84, 62, 0.1)',
          border: `1px solid ${isPass ? 'rgba(63, 183, 127, 0.3)' : 'rgba(224, 84, 62, 0.3)'}`,
          padding: '12px', borderRadius: '8px', textAlign: 'center', height: '100%'
        }}>
          {isPass ? (
            <ShieldCheck size={28} style={{ color: 'var(--accent-green)', margin: '0 auto 4px' }} />
          ) : (
            <ShieldAlert size={28} style={{ color: 'var(--accent-red)', margin: '0 auto 4px' }} />
          )}
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SERTİFİKASYON DURUMU</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: isPass ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {results.overall_status}
          </div>
        </div>

        {/* Minimum MoS - THE GAUGE */}
        <div style={{ background: 'var(--bg-input)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '16px', height: '100%' }}>
          {/* Circular Gauge */}
          <div style={{
            width: '60px', height: '60px', borderRadius: '50%',
            background: `conic-gradient(${gaugeColor} ${gaugePercent}%, var(--border-color) ${gaugePercent}%)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            boxShadow: 'inset 0 0 10px rgba(0,0,0,0.5)'
          }}>
            <div style={{ width: '48px', height: '48px', background: 'var(--bg-input)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: gaugeColor }}>
                {mos > 99 ? '∞' : mos.toFixed(2)}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>GÜVENLİK MARJI GÖSTERGESİ</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: gaugeColor }}>
              {mos > 99 ? '> 99.0' : mos.toFixed(3)}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MIL-HDBK-17 Kriteri</div>
          </div>
        </div>

        {/* Performance & Mesh */}
        <div style={{ background: 'var(--bg-input)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', height: '100%' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SİMÜLASYON SÜRESİ</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-mono)' }}>
            <Cpu size={16} /> {results.computation_time_ms.toFixed(1)} ms
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {results.mesh_summary.n_elements} Eleman | {results.mesh_summary.n_nodes} Düğüm
          </div>
        </div>

      </div>
    </div>
  );
};
