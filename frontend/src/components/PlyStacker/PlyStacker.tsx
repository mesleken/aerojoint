import React from 'react';
import { PlyInput, MaterialOption } from '../../types/analysis';
import { Plus, Trash2, Layers } from 'lucide-react';

interface Props {
  plies: PlyInput[];
  materials: MaterialOption[];
  onChange: (plies: PlyInput[]) => void;
}

export const PlyStacker: React.FC<Props> = ({ plies, materials, onChange }) => {
  const addPly = (angle: number) => {
    const defaultMat = materials[0]?.id || 'T300_5208';
    const thickness = materials.find(m => m.id === defaultMat)?.ply_thickness || 0.125;
    onChange([...plies, { material_id: defaultMat, angle, thickness }]);
  };

  const updatePly = (index: number, field: keyof PlyInput, rawVal: any) => {
    const updated = [...plies];
    if (field === 'material_id') {
      updated[index] = { ...updated[index], material_id: rawVal };
    } else {
      const val = rawVal === '' ? 0 : parseFloat(rawVal);
      updated[index] = { ...updated[index], [field]: isNaN(val) ? 0 : val };
    }
    onChange(updated);
  };

  const removePly = (index: number) => {
    onChange(plies.filter((_, i) => i !== index));
  };

  const totalThickness = plies.reduce((sum, p) => sum + p.thickness, 0).toFixed(3);

  return (
    <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div>
        <div className="section-title">
          <Layers size={16} /> Katman Dizilimi Parametreleri (Ply Stacker & Layup)
        </div>
        <p className="param-description">
          Laminatı oluşturan tekil kompozit katmanların (plies) dizilim sırasını, elyaf açılarını ve malzeme türlerini tanımlar.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginRight: '4px' }}>Hızlı Katman Ekle:</span>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => addPly(0)}>+ 0° Elyaf</button>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => addPly(45)}>+ 45° Elyaf</button>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => addPly(-45)}>+ -45° Elyaf</button>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => addPly(90)}>+ 90° Elyaf</button>
      </div>

      {/* Sütun Başlıkları ve Açıklamaları */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '40px 2fr 1.3fr 1.3fr 40px',
        gap: '10px',
        fontSize: '0.75rem',
        fontWeight: 600,
        color: 'var(--text-secondary)',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '6px'
      }}>
        <span>Sıra</span>
        <span>Malzeme Türü (MIL-HDBK-17)</span>
        <span>Elyaf Açısı (° Derece)</span>
        <span>Kalınlık (mm)</span>
        <span>Sil</span>
      </div>

      {/* Katman Dizilim Listesi */}
      <div style={{ maxHeight: '250px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {plies.map((ply, idx) => (
          <div key={idx} style={{
            display: 'grid',
            gridTemplateColumns: '40px 2fr 1.3fr 1.3fr 40px',
            gap: '10px',
            alignItems: 'center',
            background: 'var(--bg-input)',
            padding: '6px 10px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)'
          }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>#{idx + 1}</span>
            
            <select
              className="form-select"
              style={{ padding: '6px 8px', fontSize: '0.85rem' }}
              value={ply.material_id}
              onChange={(e) => updatePly(idx, 'material_id', e.target.value)}
              title="Kompozit prepreg malzeme seçimi"
            >
              {materials.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input
                type="number"
                className="form-input"
                style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem', textAlign: 'center', minWidth: '70px' }}
                value={ply.angle}
                onFocus={(e) => e.target.select()}
                onChange={(e) => updatePly(idx, 'angle', e.target.value)}
                title="Katman elyaf yönlenme açısı (°)"
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>°</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input
                type="number"
                step="0.001"
                className="form-input"
                style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem', textAlign: 'center', minWidth: '70px' }}
                value={ply.thickness === 0 ? '' : ply.thickness}
                onFocus={(e) => e.target.select()}
                onChange={(e) => updatePly(idx, 'thickness', e.target.value)}
                title="Tekil katman nominal kalınlığı (mm)"
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>mm</span>
            </div>

            <button
              style={{ background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', display: 'flex', justifyContent: 'center' }}
              onClick={() => removePly(idx)}
              title="Katmanı kaldır"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '4px', fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
        <span>Toplam Katman Adedi: <b>{plies.length} Ply</b></span>
        <span>Toplam Laminat Kalınlığı (t): <b>{totalThickness} mm</b></span>
      </div>
    </div>
  );
};
