"""
ZYNORA-ML — FastAPI Main Application Entrypoint
================================================
Boots the FastAPI server and triggers ML model training on startup.

STARTUP SEQUENCE (what happens when you run the backend):
  1. FastAPI creates the app instance
  2. CORS middleware configured (allows frontend at localhost:5173)
  3. All routers mounted under /api prefix
  4. @startup event fires → ModelRegistry.startup_train()
     → Downloads Bengaluru Housing Dataset
     → Trains RandomForestRegressor (R² ~0.85-0.92)
     → Trains KMeans(n_clusters=5) (Silhouette ~0.28-0.42)
     → Saves .joblib model files to backend/models/
  5. App is ready to serve requests

HOW TO START THE BACKEND (in Antigravity IDE terminal):
  python backend/run_backend.py
  OR
  uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

WATCH FOR THESE LOGS ON STARTUP:
  ✅ RandomForest R² Score: 0.XXX
  ✅ KMeans Silhouette Score: 0.XXX
  ✅ Models saved to backend/models/
"""
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path regardless of whether invoked from root or backend/
_root_dir = str(Path(__file__).resolve().parent.parent.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.api.routes_projects import router as projects_router
from backend.app.api.routes_floorplans import router as floorplans_router
from backend.app.api.routes_ml import router as ml_router
from backend.app.api.routes_design import router as design_router
from backend.app.api.routes_render import router as render_router
from backend.app.api.routes_ai import router as ai_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler — runs startup tasks before serving requests.

    MANUAL STEP: This is equivalent to running:
      from backend.app.ml.model_registry import ModelRegistry
      ModelRegistry.get_instance().startup_train()
    ...automatically on every server start.
    """
    # ── STARTUP ───────────────────────────────────────────────────────────────
    logger.info("ZYNORA-ML Backend starting...")
    logger.info("Initialising ML model training pipeline...")

    try:
        from backend.app.ml.model_registry import ModelRegistry
        registry = ModelRegistry.get_instance()
        registry.startup_train()
        logger.info(
            f"ML Pipeline ready | RF R²={registry.rf_r2} | "
            f"KMeans Silhouette={registry.kmeans_silhouette}"
        )
    except Exception as e:
        logger.error(f"ML training failed (will use fallback values): {e}")

    yield   # ← App serves requests here

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("ZYNORA-ML Backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Machine Learning & Architectural Intelligence Backend for ZYNORA-ML. "
        "Trained on real Indian residential housing data (Bengaluru, 13,320 records). "
        "ML: RandomForest + KMeans + NSGA-II + Vastu Shastra scoring."
    ),
    lifespan=lifespan,
)

# Configure CORS (allows React frontend on port 5173 to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api prefix
app.include_router(projects_router,  prefix=settings.API_PREFIX)
app.include_router(floorplans_router,prefix=settings.API_PREFIX)
app.include_router(ml_router,        prefix=settings.API_PREFIX)
app.include_router(design_router,    prefix=settings.API_PREFIX)
app.include_router(render_router,    prefix=settings.API_PREFIX)
app.include_router(ai_router,        prefix=settings.API_PREFIX)


@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Health check endpoint. Also reports ML model training status.
    Open this in browser: http://127.0.0.1:8000/health
    """
    try:
        from backend.app.ml.model_registry import ModelRegistry
        reg = ModelRegistry.get_instance()
        ml_status = {
            "status":         "TRAINED" if reg.is_trained else "FALLBACK",
            "rfR2Score":      reg.rf_r2,
            "kmeansSilhouette": reg.kmeans_silhouette,
            "dataset":        "Bengaluru House Data (India)",
            "totalSamples":   reg.dataset_size,
        }
    except Exception:
        ml_status = {"status": "INITIALISING"}

    return {
        "status":        "healthy",
        "service":       "ZYNORA-ML Backend",
        "version":       settings.VERSION,
        "mlCoreStatus":  ml_status,
        "endpoints": {
            "aiStatus":           f"{settings.API_PREFIX}/ai/status",
            "aiGenerate":         f"{settings.API_PREFIX}/ai/generate-floorplan",
            "aiRequirements":     f"{settings.API_PREFIX}/ai/requirements",
            "aiModify":           f"{settings.API_PREFIX}/ai/modify",
            "aiImageAnalysis":    f"{settings.API_PREFIX}/ai/analyze-floorplan-image",
            "generateFloorplans": f"{settings.API_PREFIX}/floorplans/generate",
            "mlModelInfo":        f"{settings.API_PREFIX}/ml/model-info",
            "vastuAnalysis":      f"{settings.API_PREFIX}/ml/vastu-analysis",
            "explainModel":       f"{settings.API_PREFIX}/ml/explain",
        }
    }

