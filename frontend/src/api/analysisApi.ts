import { AnalysisRequest, AnalysisResponse, MaterialOption, CustomMaterialPayload } from '../types/analysis';

const API_BASE = 'http://localhost:8000/api';

export async function fetchMaterials(): Promise<MaterialOption[]> {
  try {
    const res = await fetch(`${API_BASE}/materials`);
    if (!res.ok) throw new Error('Malzemeler alınamadı');
    const data = await res.json();
    return data.materials || [];
  } catch (err) {
    console.warn('Backend API ulaşılamadı, varsayılan malzeme kütüphanesi kullanılacak.');
    return [
      { id: 'T300_5208', name: 'T300/5208 Carbon/Epoxy', category: 'Carbon/Epoxy', source: 'MIL-HDBK-17-2F', ply_thickness: 0.125 },
      { id: 'AS4_3501_6', name: 'AS4/3501-6 Carbon/Epoxy', category: 'Carbon/Epoxy', source: 'CMH-17-2G', ply_thickness: 0.188 },
      { id: 'IM7_8552', name: 'IM7/8552 Carbon/Epoxy', category: 'Carbon/Epoxy', source: 'CMH-17-2G', ply_thickness: 0.131 },
      { id: 'E_GLASS_EPOXY', name: 'E-Glass/Epoxy', category: 'Glass/Epoxy', source: 'Daniel & Ishai', ply_thickness: 0.250 }
    ];
  }
}

export async function addCustomMaterial(mat: CustomMaterialPayload): Promise<void> {
  const res = await fetch(`${API_BASE}/materials/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mat)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Malzeme eklenemedi' }));
    throw new Error(errData.detail || 'Malzeme eklenemedi');
  }
}

export async function deleteCustomMaterial(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/materials/${encodeURIComponent(id)}`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Malzeme silinemedi' }));
    throw new Error(errData.detail || 'Malzeme silinemedi');
  }
}

export async function runAnalysis(req: AnalysisRequest): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req)
  });
  
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Sunucu hatası' }));
    throw new Error(errData.detail || 'Analiz çalıştırılamadı');
  }
  
  return res.json();
}

export async function downloadPdfReport(req: AnalysisRequest): Promise<Blob> {
  const res = await fetch(`${API_BASE}/reports/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'PDF oluşturulamadı' }));
    throw new Error(errData.detail || 'PDF oluşturulamadı');
  }
  return res.blob();
}
