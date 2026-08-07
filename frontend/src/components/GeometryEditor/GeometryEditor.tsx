import React from 'react';
import { HoleInput } from '../../types/analysis';
import { Sliders, Plus, Trash2 } from 'lucide-react';

interface Props {
  width: number;
  height: number;
  holes: HoleInput[];
  constraintType: string;
  meshGlobal: number;
  meshHole: number;
  onChangeWidth: (w: number) => void;
  onChangeHeight: (h: number) => void;
  onChangeHoles: (holes: HoleInput[]) => void;
  onChangeConstraint: (c: string) => void;
  onChangeMeshGlobal: (m: number) => void;
  onChangeMeshHole: (m: number) => void;
}

export const GeometryEditor: React.FC<Props> = ({
  width, height, holes, constraintType, meshGlobal, meshHole,
  onChangeWidth, onChangeHeight, onChangeHoles, onChangeConstraint,
  onChangeMeshGlobal, onChangeMeshHole
}) => {
  const addHole = () => {
    onChangeHoles([
      ...holes,
      { x: Math.round(width / 2), y: Math.round(height / 2), diameter: 6.35, load_magnitude: 5000, load_angle: 0 }
    ]);
  };

  const updateHole = (index: number, field: keyof HoleInput, rawVal: string) => {
    const updated = [...holes];
    const val = rawVal === '' ? 0 : parseFloat(rawVal);
    updated[index] = { ...updated[index], [field]: isNaN(val) ? 0 : val };
    onChangeHoles(updated);
  };

  const removeHole = (index: number) => {
    onChangeHoles(holes.filter((_, i) => i !== index));
  };

  const parseVal = (rawVal: string, fallback: number = 0) => {
    if (rawVal === '') return 0;
    const num = parseFloat(rawVal);
    return isNaN(num) ? fallback : num;
  };

  return (
    <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div>
        <div className="section-title">
          <Sliders size={16} /> Geometri, Yük & Mesh Parametreleri
        </div>
        <p className="param-description">
          Kompozit panelin fiziksel boyutlarını, pimli bağlantı deliklerinin yerini, uygulanan yataklama (bearing) kuvvetlerini ve sınır koşullarını tanımlar.
        </p>
      </div>

      {/* Plaka Boyutları */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div className="form-group">
          <label className="form-label">Plaka Genişliği (W - mm)</label>
          <input
            type="number" className="form-input"
            value={width === 0 ? '' : width}
            onFocus={(e) => e.target.select()}
            onChange={(e) => onChangeWidth(parseVal(e.target.value, 100))}
            title="Kompozit panelin X eksenindeki toplam genişliği (mm)"
          />
          <span className="param-description">Kompozit panelin X eksenindeki toplam uzunluğu</span>
        </div>
        <div className="form-group">
          <label className="form-label">Plaka Yüksekliği (H - mm)</label>
          <input
            type="number" className="form-input"
            value={height === 0 ? '' : height}
            onFocus={(e) => e.target.select()}
            onChange={(e) => onChangeHeight(parseVal(e.target.value, 50))}
            title="Kompozit panelin Y eksenindeki toplam yüksekliği (mm)"
          />
          <span className="param-description">Kompozit panelin Y eksenindeki toplam eni</span>
        </div>
      </div>

      {/* Sınır Koşulları ve Mesh Yoğunluğu */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div className="form-group">
          <label className="form-label">Sınır Koşulu (Mechanical Boundary)</label>
          <select
            className="form-select"
            value={constraintType} onChange={(e) => onChangeConstraint(e.target.value)}
          >
            <option value="fixed">Sol Kenar Tam Ankastre (Fixed: U_x=0, U_y=0)</option>
            <option value="roller_x">Sol Kenar Y-Serbest (Roller: U_x=0)</option>
          </select>
          <span className="param-description">Plakanın sol kenarındaki mekanik tutturma tipi</span>
        </div>
        <div className="form-group">
          <label className="form-label">Mesh Yoğunluğu (Global / Delik - mm)</label>
          <div style={{ display: 'flex', gap: '6px' }}>
            <input
              type="number" className="form-input" style={{ width: '50%' }}
              value={meshGlobal === 0 ? '' : meshGlobal}
              onFocus={(e) => e.target.select()}
              onChange={(e) => onChangeMeshGlobal(parseVal(e.target.value, 5))}
              title="Genel Plaka Mesh Boyutu (mm)"
            />
            <input
              type="number" className="form-input" style={{ width: '50%' }}
              value={meshHole === 0 ? '' : meshHole}
              onFocus={(e) => e.target.select()}
              onChange={(e) => onChangeMeshHole(parseVal(e.target.value, 1))}
              title="Delik Çevresi Radyal Mesh Boyutu (mm)"
            />
          </div>
          <span className="param-description">Soldaki: Genel plaka mesh boyutu | Sağdaki: Delik çevresi sıklaştırma boyutu</span>
        </div>
      </div>

      {/* Delik Matrisi Tablosu */}
      <div style={{ marginTop: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Pimli Bağlantı Delikleri & Yataklama Yükleri</span>
            <p className="param-description">Deliklerin X ve Y koordinatları (mm), çapı D (mm), pim yataklama kuvveti P (N) ve yük açısı θ (°)</p>
          </div>
          <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={addHole}>
            <Plus size={12} /> Delik Ekle
          </button>
        </div>

        {holes.length === 0 ? (
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Plakada delik tanımlanmadı. (Düz plaka analizi)</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* Delik Tablo Başlıkları */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr) 30px',
              gap: '6px',
              fontSize: '0.7rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              borderBottom: '1px solid var(--border-color)',
              paddingBottom: '4px'
            }}>
              <span>X Konumu (mm)</span>
              <span>Y Konumu (mm)</span>
              <span>Çap D (mm)</span>
              <span>Yük P (N)</span>
              <span>Yük Açısı (°)</span>
              <span>Sil</span>
            </div>

            {holes.map((hole, idx) => (
              <div key={idx} style={{
                background: 'var(--bg-input)', padding: '6px 8px', borderRadius: '6px',
                border: '1px solid var(--border-color)', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr) 30px', gap: '6px', alignItems: 'center'
              }}>
                <input
                  type="number" className="form-input" placeholder="X (mm)"
                  value={hole.x === 0 ? '' : hole.x}
                  onFocus={(e) => e.target.select()}
                  onChange={(e) => updateHole(idx, 'x', e.target.value)}
                  title={`Delik X koordinatı (0 - ${width} mm)`}
                />
                <input
                  type="number" className="form-input" placeholder="Y (mm)"
                  value={hole.y === 0 ? '' : hole.y}
                  onFocus={(e) => e.target.select()}
                  onChange={(e) => updateHole(idx, 'y', e.target.value)}
                  title={`Delik Y koordinatı (0 - ${height} mm)`}
                />
                <input
                  type="number" className="form-input" placeholder="D (mm)"
                  value={hole.diameter === 0 ? '' : hole.diameter}
                  onFocus={(e) => e.target.select()}
                  onChange={(e) => updateHole(idx, 'diameter', e.target.value)}
                  title="Delik Çapı D (mm)"
                />
                <input
                  type="number" className="form-input" placeholder="P (N)"
                  value={hole.load_magnitude === 0 ? '' : hole.load_magnitude}
                  onFocus={(e) => e.target.select()}
                  onChange={(e) => updateHole(idx, 'load_magnitude', e.target.value)}
                  title="Pim Yataklama Kuvveti P (Newton)"
                />
                <input
                  type="number" className="form-input" placeholder="Açı (°)"
                  value={hole.load_angle}
                  onFocus={(e) => e.target.select()}
                  onChange={(e) => updateHole(idx, 'load_angle', e.target.value)}
                  title="Kuvvet Uygulama Açısı (Derece)"
                />
                <button
                  className="btn btn-secondary"
                  style={{ padding: '4px', color: '#ef4444', display: 'flex', justifyContent: 'center' }}
                  onClick={() => removeHole(idx)}
                  title="Deliği Sil"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
