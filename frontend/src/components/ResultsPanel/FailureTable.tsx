import React from 'react';
import { PlyResult } from '../../types/analysis';

interface Props {
  plyResults: PlyResult[];
  criticalPlyIndex: number;
}

export const FailureTable: React.FC<Props> = ({ plyResults, criticalPlyIndex }) => {
  return (
    <div className="glass-panel" style={{ padding: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Katman Bazlı Kırılma ve Hashin/Tsai-Wu Değerlendirmesi
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--accent-amber)', background: 'rgba(245, 158, 11, 0.15)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
          ⚠️ : En Yüksek Hasar İndeksli Kritik Katman (Critical Ply)
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '6px 10px' }}>Katman #</th>
              <th style={{ padding: '6px 10px' }}>Açı (°)</th>
              <th style={{ padding: '6px 10px' }}>Hashin Max FI</th>
              <th style={{ padding: '6px 10px' }}>Baskın Mod (Hashin)</th>
              <th style={{ padding: '6px 10px' }}>Tsai-Wu FI</th>
              <th style={{ padding: '6px 10px' }}>MoS (Hashin)</th>
              <th style={{ padding: '6px 10px' }}>Durum</th>
            </tr>
          </thead>
          <tbody>
            {plyResults.map((p) => {
              const isCrit = p.ply_id === criticalPlyIndex;
              return (
                <tr
                  key={p.ply_id}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    background: isCrit ? 'rgba(245, 158, 11, 0.12)' : 'transparent',
                    fontWeight: isCrit ? 600 : 400
                  }}
                >
                  <td style={{ padding: '6px 10px' }}>#{p.ply_id + 1} {isCrit && '⚠️'}</td>
                  <td style={{ padding: '6px 10px' }}>{p.angle}°</td>
                  <td style={{ padding: '6px 10px', color: p.hashin_max_fi >= 1.0 ? '#f87171' : 'inherit' }}>
                    {p.hashin_max_fi.toFixed(4)}
                  </td>
                  <td style={{ padding: '6px 10px', color: 'var(--accent-cyan)' }}>{p.dominant_mode}</td>
                  <td style={{ padding: '6px 10px' }}>{p.tsai_wu_fi.toFixed(4)}</td>
                  <td style={{ padding: '6px 10px', color: p.mos_hashin >= 0 ? '#34d399' : '#f87171' }}>
                    {p.mos_hashin.toFixed(3)}
                  </td>
                  <td style={{ padding: '6px 10px' }}>
                    <span className={`badge ${p.is_failed ? 'badge-fail' : 'badge-pass'}`}>
                      {p.is_failed ? 'FAIL' : 'PASS'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
