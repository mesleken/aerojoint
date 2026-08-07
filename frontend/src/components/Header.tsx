import React from 'react';
import { Plane, ShieldCheck, FileText } from 'lucide-react';

interface Props {
  onRunAnalysis: () => void;
  loading: boolean;
  onExportPdf?: () => void;
}

export const Header: React.FC<Props> = ({ onRunAnalysis, loading }) => {
  return (
    <header className="header">
      <div className="logo-group">
        <Plane className="w-6 h-6 text-blue-500" style={{ color: '#3b82f6' }} />
        <span className="logo-title">AeroJoint</span>
        <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: '8px' }}>
          v1.0 (MIL-HDBK-17 Uyumlu)
        </span>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
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
