"""
ZYNORA-ML Backend Configuration
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field

# Load .env file from backend root or repository root if present
try:
    from dotenv import load_dotenv

    _base_dir = Path(__file__).resolve().parent.parent.parent
    _env_candidates = [
        _base_dir / ".env",
        _base_dir.parent / ".env",
    ]
    for _env_path in _env_candidates:
        if _env_path.is_file():
            load_dotenv(_env_path, override=False)
            break
except ImportError:
    pass


class Settings(BaseModel):
    PROJECT_NAME: str = "ZYNORA-ML Spatial Intelligence Core"
    VERSION: str = "0.2.0"
    API_PREFIX: str = "/api"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]
    DATA_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_storage"
    )

    # Google Gemini AI Layer (read strictly from backend environment)
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip())
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip())

    # Architectural Engine Flags
    ZYNORA_AI_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("ZYNORA_AI_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    ZYNORA_MAX_CANDIDATES: int = Field(
        default_factory=lambda: int(os.getenv("ZYNORA_MAX_CANDIDATES", "3"))
    )
    ZYNORA_DEFAULT_UNIT: str = Field(
        default_factory=lambda: os.getenv("ZYNORA_DEFAULT_UNIT", "ft")
    )
    ZYNORA_ENABLE_VASTU: bool = Field(
        default_factory=lambda: os.getenv("ZYNORA_ENABLE_VASTU", "true").lower() in ("true", "1", "yes")
    )
    ZYNORA_ENABLE_3D: bool = Field(
        default_factory=lambda: os.getenv("ZYNORA_ENABLE_3D", "true").lower() in ("true", "1", "yes")
    )
    ZYNORA_ENABLE_BLENDER: bool = Field(
        default_factory=lambda: os.getenv("ZYNORA_ENABLE_BLENDER", "true").lower() in ("true", "1", "yes")
    )

    @property
    def has_gemini_api_key(self) -> bool:
        return bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY) > 10)


settings = Settings()
