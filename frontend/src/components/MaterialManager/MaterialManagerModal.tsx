import React, { useState } from 'react';
import { MaterialOption, CustomMaterialPayload } from '../../types/analysis';
import { addCustomMaterial, deleteCustomMaterial } from '../../api/analysisApi';
import { Plus, Trash2, X, Database } from 'lucide-react';

interface MaterialManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  materials: MaterialOption[];
  onRefreshMaterials: () => void;
}

export const MaterialManagerModal: React.FC<MaterialManagerModalProps> = ({
  isOpen,
  onClose,
  materials,
  onRefreshMaterials
}) => {
  const [activeTab, setActiveTab] = useState<'list' | 'add'>('list');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form State
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Carbon/Epoxy');
  const [source, setSource] = useState('Proprietary / User Defined');
  const [plyThickness, setPlyThickness] = useState(0.125);
  
  // Elastic Properties
  const [E1, setE1] = useState(135000);
  const [E2, setE2] = useState(9000);
  const [G12, setG12] = useState(5000);
  const [nu12, setNu12] = useState(0.3);

  // Strength Properties
  const [Xt, setXt] = useState(1500);
  const [Xc, setXc] = useState(1200);
  const [Yt, setYt] = useState(50);
  const [Yc, setYc] = useState(200);
  const [S12, setS12] = useState(70);

  if (!isOpen) return null;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!id.trim() || !name.trim()) {
      setError('Lütfen benzersiz ID ve Malzeme Adı giriniz.');
      return;
    }

    const payload: CustomMaterialPayload = {
      id: id.trim().toUpperCase().replace(/\s+/g, '_'),
      name: name.trim(),
      category: category.trim(),
      source: source.trim(),
      ply_thickness: Number(plyThickness),
      elastic: {
        E1: Number(E1),
        E2: Number(E2),
        G12: Number(G12),
        nu12: Number(nu12)
      },
      strength: {
        Xt: Number(Xt),
        Xc: Number(Xc),
        Yt: Number(Yt),
        Yc: Number(Yc),
        S12: Number(S12)
      }
    };

    try {
      await addCustomMaterial(payload);
      setSuccess(`'${payload.name}' malzemesi başarıyla kütüphaneye eklendi.`);
      onRefreshMaterials();
      setActiveTab('list');
      // Reset form
      setId('');
      setName('');
    } catch (err: any) {
      setError(err.message || 'Malzeme eklenirken bir hata oluştu.');
    }
  };

  const handleDelete = async (matId: string) => {
    if (!window.confirm(`'${matId}' malzemesini silmek istediğinizden emin misiniz?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteCustomMaterial(matId);
      setSuccess(`'${matId}' malzemesi silindi.`);
      onRefreshMaterials();
    } catch (err: any) {
      setError(err.message || 'Silme işlemi başarısız.');
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="glass-panel" style={{
        width: '90%', maxWidth: '750px', maxHeight: '85vh', overflowY: 'auto',
        borderRadius: '12px', border: '1px solid var(--border-color)',
        background: '#0f172a', padding: '24px', color: '#f8fafc'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={22} style={{ color: '#38bdf8' }} />
            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Kompozit Malzeme Kütüphanesi Yöneticisi</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid #1e293b', paddingBottom: '12px', marginBottom: '16px' }}>
          <button
            className={`btn ${activeTab === 'list' ? 'btn-primary' : ''}`}
            style={{ padding: '6px 16px', borderRadius: '6px', fontSize: '0.85rem' }}
            onClick={() => setActiveTab('list')}
          >
            Mevcut Malzemeler ({materials.length})
          </button>
          <button
            className={`btn ${activeTab === 'add' ? 'btn-primary' : ''}`}
            style={{ padding: '6px 16px', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            onClick={() => setActiveTab('add')}
          >
            <Plus size={16} /> Yeni Özel Malzeme Ekle (Custom Prepreg)
          </button>
        </div>

        {/* Notifications */}
        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', padding: '10px 14px', borderRadius: '6px', marginBottom: '14px', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}
        {success && (
          <div style={{ background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80', padding: '10px 14px', borderRadius: '6px', marginBottom: '14px', fontSize: '0.85rem' }}>
            {success}
          </div>
        )}

        {/* TAB 1: LIST */}
        {activeTab === 'list' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {materials.map((m) => (
              <div key={m.id} style={{
                background: '#1e293b', padding: '12px 16px', borderRadius: '8px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center'
              }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#f1f5f9' }}>
                    {m.name} <span style={{ fontSize: '0.75rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 6px', borderRadius: '4px', marginLeft: '6px' }}>{m.id}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                    Kategori: {m.category} | Kaynak: {m.source} | Kalınlık: {m.ply_thickness} mm
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(m.id)}
                  style={{ background: 'rgba(239, 68, 68, 0.2)', border: 'none', color: '#f87171', padding: '6px 10px', borderRadius: '6px', cursor: 'pointer' }}
                  title="Malzemeyi Sil"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* TAB 2: ADD FORM */}
        {activeTab === 'add' && (
          <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ gridColumn: 'span 1' }}>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Malzeme ID (ör: MY_CARBON_01)</label>
              <input type="text" value={id} onChange={(e) => setId(e.target.value)} required placeholder="MY_CARBON_01" style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Malzeme Adı</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="Custom High Modulus Carbon" style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Kategori</label>
              <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div style={{ gridColumn: 'span 1' }}>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Varsayılan Katman Kalınlığı (mm)</label>
              <input type="number" step="0.001" value={plyThickness} onChange={(e) => setPlyThickness(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            {/* ELASTİSİTE MODÜLLERİ */}
            <div style={{ gridColumn: 'span 2', fontWeight: 600, borderBottom: '1px solid #334155', paddingBottom: '4px', marginTop: '8px', color: '#38bdf8' }}>
              Elastik Özellikler (MPa)
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>E1 (Boyuna Modül, MPa)</label>
              <input type="number" value={E1} onChange={(e) => setE1(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>E2 (Enine Modül, MPa)</label>
              <input type="number" value={E2} onChange={(e) => setE2(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>G12 (Kayma Modülü, MPa)</label>
              <input type="number" value={G12} onChange={(e) => setG12(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>ν12 (Poisson Oranı)</label>
              <input type="number" step="0.01" value={nu12} onChange={(e) => setNu12(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            {/* MUKAVEMET DEĞERLERİ */}
            <div style={{ gridColumn: 'span 2', fontWeight: 600, borderBottom: '1px solid #334155', paddingBottom: '4px', marginTop: '8px', color: '#38bdf8' }}>
              Dayanım Değerleri / Allowables (MPa)
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Xt (Boyuna Çekme, MPa)</label>
              <input type="number" value={Xt} onChange={(e) => setXt(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Xc (Boyuna Basma, MPa)</label>
              <input type="number" value={Xc} onChange={(e) => setXc(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Yt (Enine Çekme, MPa)</label>
              <input type="number" value={Yt} onChange={(e) => setYt(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Yc (Enine Basma, MPa)</label>
              <input type="number" value={Yc} onChange={(e) => setYc(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>S12 (Enine Kayma, MPa)</label>
              <input type="number" value={S12} onChange={(e) => setS12(parseFloat(e.target.value) || 0)} style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#1e293b', border: '1px solid #334155', color: '#fff' }} />
            </div>

            <div style={{ gridColumn: 'span 2', marginTop: '12px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button type="button" onClick={() => setActiveTab('list')} className="btn" style={{ padding: '8px 16px' }}>İptal</button>
              <button type="submit" className="btn btn-primary" style={{ padding: '8px 24px' }}>Kaydet ve Kütüphaneye Ekle</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
