import React from 'react';
import { Plane, ShieldCheck, FileText, Database, Download, History, Bookmark } from 'lucide-react';
import { useAnalysisStore } from '../store/useAnalysisStore';

interface Props {
  onRunAnalysis: () => void;
  loading: boolean;
  onOpenMaterialManager?: () => void;
  onOpenCadStudio?: () => void;
  onOpenHistory?: () => void;
  onExportPdf?: () => void;
}

export const Header: React.FC<Props> = ({ onRunAnalysis, loading, onOpenMaterialManager, onOpenCadStudio, onOpenHistory, onExportPdf }) => {
  const applyTemplate = useAnalysisStore(state => state.applyTemplate);

  return (
    <header className="header">
      <div className="logo-group">
        <Plane className="w-6 h-6 text-blue-500" style={{ color: '#3b82f6' }} />
        <span className="logo-title">AeroJoint</span>
        <span style={{ fontSize: '0.75rem', color: '#38bdf8', marginLeft: '8px', fontWeight: 600, background: 'rgba(56, 189, 248, 0.15)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
          v4.0-beta
        </span>
      </div>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        {/* Template Quick Loader */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--bg-input)', padding: '2px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.75rem' }}>
          <Bookmark size={14} style={{ color: '#f59e0b' }} />
          <select
            onChange={(e) => {
              if (e.target.value) {
                applyTemplate(e.target.value as any);
                e.target.value = '';
              }
            }}
            defaultValue=""
            style={{ background: 'transparent', color: 'var(--text-main)', border: 'none', cursor: 'pointer', fontSize: '0.75rem', outline: 'none' }}
          >
            <option value="" disabled>🚀 Örnek Şablon Yükle...</option>
            <option value="NASA_QI">NASA T300/5208 Quasi-Isotropic</option>
            <option value="TENSION_DOMINATED">Çekme Baskın Lug (Tension-Dominated)</option>
            <option value="DUAL_HOLE">Çift Delikli Bağlantı Kulaklığı</option>
          </select>
        </div>

        {onOpenHistory && (
          <button
            className="btn btn-secondary"
            onClick={onOpenHistory}
            title="Geçmiş Analiz Kayıtları ve Audit Trail"
          >
            <History size={16} /> Analiz Geçmişi
          </button>
        )}

        {onOpenCadStudio && (
          <button
            className="btn btn-secondary"
            onClick={onOpenCadStudio}
            style={{ background: '#0284c7', color: '#ffffff', borderColor: '#38bdf8' }}
            title="3B CAD & FEM Yük Entegrasyon Stüdyosu"
          >
            <Database size={16} /> 3B CAD Stüdyosu
          </button>
        )}
        {onOpenMaterialManager && (
          <button
            className="btn btn-secondary"
            onClick={onOpenMaterialManager}
            title="Özel Malzeme Ekle / Düzenle"
          >
            <Database size={16} /> Malzemeler
          </button>
        )}
        {onExportPdf && (
          <button
            className="btn btn-secondary"
            onClick={onExportPdf}
            title="PDF Sertifikasyon Raporu İndir"
          >
            <Download size={16} /> PDF Rapor
          </button>
        )}
        <button
          className="btn btn-primary"
          onClick={onRunAnalysis}
          disabled={loading}
        >
          <ShieldCheck size={16} />
          {loading ? 'Analiz Çözülüyor...' : '▶ Analiz Et'}
        </button>
      </div>
    </header>
  );
};
