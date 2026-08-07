"""
AeroJoint Uygulama Konfigürasyonu
"""
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "AeroJoint API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

settings = Settings()
