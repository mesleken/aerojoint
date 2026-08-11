import React from 'react';
import { Plane, ShieldCheck, FileText, Database, Download } from 'lucide-react';

interface Props {
  onRunAnalysis: () => void;
  loading: boolean;
  onOpenMaterialManager?: () => void;
  onOpenCadStudio?: () => void;
  onExportPdf?: () => void;
}

export const Header: React.FC<Props> = ({ onRunAnalysis, loading, onOpenMaterialManager, onOpenCadStudio, onExportPdf }) => {
  return (
    <header className="header">
      <div className="logo-group">
        <Plane className="w-6 h-6 text-blue-500" style={{ color: '#3b82f6' }} />
        <span className="logo-title">AeroJoint</span>
        <span style={{ fontSize: '0.75rem', color: '#38bdf8', marginLeft: '8px', fontWeight: 600 }}>
          v3.0 (3B CAD & PDM)
        </span>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
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
            <Database size={16} /> Malzeme Kütüphanesi
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
          className="btn btn-secondary"
          onClick={() => window.open('http://localhost:8000/docs', '_blank')}
        >
          <FileText size={16} /> API Docs
        </button>
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
