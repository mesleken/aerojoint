import React from 'react';
import { AnalysisResponse } from '../../types/analysis';
import { ShieldCheck, ShieldAlert, Cpu, Layers } from 'lucide-react';

interface Props {
  results: AnalysisResponse;
}

export const ResultsSummary: React.FC<Props> = ({ results }) => {
  const isPass = results.overall_status === 'PASS';

  return (
    <div className="glass-panel" style={{ padding: '14px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', alignItems: 'center' }}>
        
        {/* Status Box */}
        <div style={{
          background: isPass ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${isPass ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          padding: '12px', borderRadius: '8px', textAlign: 'center'
        }}>
          {isPass ? (
            <ShieldCheck size={28} style={{ color: '#34d399', margin: '0 auto 4px' }} />
          ) : (
            <ShieldAlert size={28} style={{ color: '#f87171', margin: '0 auto 4px' }} />
          )}
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SERTİFİKASYON DURUMU</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: isPass ? '#34d399' : '#f87171' }}>
            {results.overall_status}
          </div>
        </div>

        {/* Minimum MoS */}
        <div style={{ background: 'var(--bg-input)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>MİNİMUM GÜVENLİK MARJI (MoS)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: results.min_mos >= 0 ? '#34d399' : '#f87171' }}>
            {results.min_mos.toFixed(3)}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MIL-HDBK-17 Kriteri</div>
        </div>

        {/* Governing Criterion & Mode */}
        <div style={{ background: 'var(--bg-input)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>KRİTİK HASAR MODU</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-amber)' }}>
            {results.critical_mode}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Katman #{results.critical_ply + 1} ({results.critical_angle}°)
          </div>
        </div>

        {/* Performance & Mesh */}
        <div style={{ background: 'var(--bg-input)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>SİMÜLASYON SÜRESİ</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '4px' }}>
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
