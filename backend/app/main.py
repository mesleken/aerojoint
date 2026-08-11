"""
AeroJoint — Composite Joint Analysis & Certification Software Backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.routes import analysis, materials, geometry, reports, cad

app = FastAPI(
    title=settings.APP_NAME,
    description="MIL-HDBK-17 / CMH-17 Uyumlu Kompozit Bağlantı Analiz ve Sertifikasyon Servisi",
    version=settings.VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)
app.include_router(materials.router)
app.include_router(geometry.router)
app.include_router(reports.router)
app.include_router(cad.router)

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
