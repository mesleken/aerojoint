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
    if not HAS_WEASYPRINT:
        raise HTTPException(
            status_code=501,
            detail="WeasyPrint PDF motoru sunucuda yüklü değil. PDF raporu üretilemiyor."
        )

    try:
        service = AnalysisService()
        result = service.run_full_analysis(request.dict())

        generator = CertificationReportGenerator()
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_file.close()

        pdf_path = generator.generate_pdf(result, tmp_file.name)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="AeroJoint_Certification_Report.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF rapor oluşturulamadı: {str(e)}")
