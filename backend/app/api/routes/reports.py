"""
PDF Rapor Üretim Endpoint'i
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os

from ...models.analysis import AnalysisRequest
from ...services.analysis_service import AnalysisService
from ...reports.generator import CertificationReportGenerator, HAS_WEASYPRINT

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.post("/pdf")
async def generate_pdf_report(request: AnalysisRequest):
    """Analiz parametrelerinden MIL-HDBK-17 PDF Sertifikasyon Raporu üretir."""
    try:
        service = AnalysisService()
        result = service.run_full_analysis(request.model_dump())

        generator = CertificationReportGenerator()
        suffix = ".pdf" if HAS_WEASYPRINT else ".html"
        media_type = "application/pdf" if HAS_WEASYPRINT else "text/html"
        filename = "AeroJoint_Certification_Report.pdf" if HAS_WEASYPRINT else "AeroJoint_Certification_Report.html"

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_file.close()

        out_path = generator.generate_pdf(result, tmp_file.name)

        return FileResponse(
            out_path,
            media_type=media_type,
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor oluşturulamadı: {str(e)}")
