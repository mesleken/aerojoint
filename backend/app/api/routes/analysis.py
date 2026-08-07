"""
FastAPI Analiz Endpoint'leri
"""
from fastapi import APIRouter, HTTPException
import asyncio
from ...models.analysis import AnalysisRequest, AnalysisResponse
from ...services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

@router.post("/run")
def run_analysis(request: AnalysisRequest):
    """
    Senkron kompozit bağlantı analizi çalıştırma endpoint'i.
    """
    import signal
    orig_signal = signal.signal
    try:
        signal.signal = lambda *args, **kwargs: None
    except Exception:
        pass

    try:
        service = AnalysisService()
        return service.run_full_analysis(request.dict())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz sırasında hata: {str(e)}")
    finally:
        try:
            signal.signal = orig_signal
        except Exception:
            pass
