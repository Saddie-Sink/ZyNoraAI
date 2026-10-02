"""
ZYNORA-ML Backend Configuration
"""
from pydantic import BaseModel
import os

class Settings(BaseModel):
    PROJECT_NAME: str = "ZYNORA-ML Spatial Intelligence Core"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_storage")

settings = Settings()
