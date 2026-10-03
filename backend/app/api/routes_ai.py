"""
ZYNORA AI — AI Architecture & Orchestration API Router
======================================================
Exposes production-ready AI endpoints:
  - GET  /api/ai/status                 → Model, provider, and engine health status
  - POST /api/ai/requirements           → NLU requirement extraction & validation
  - POST /api/ai/generate-floorplan     → Full 16-stage pipeline (prompt → validated candidates)
  - POST /api/ai/analyze-floorplan-image→ Gemini vision image understanding & vector synthesis
  - POST /api/ai/modify                 → Conversational design operations & local geometric edits
"""
import base64
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body, Request

from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.ai.schemas import (
    RequirementsRequest,
    RequirementsResponse,
    GenerateFloorplanRequest,
    ModifyFloorplanRequest,
    AIStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])
orchestrator = AIOrchestrator()


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status():
    """
    Returns the real-time configuration status of the AI interpretation layer,
    configured model, and active deterministic geometric engines.
    """
    status_data = orchestrator.get_status()
    return AIStatusResponse(**status_data)


@router.post("/requirements", response_model=RequirementsResponse)
def extract_house_requirements(payload: RequirementsRequest):
    """
    Converts a natural-language architectural request into standardized,
    machine-readable HouseRequirements.
    """
    try:
        reqs, validation = orchestrator.extract_requirements(
            prompt=payload.prompt,
            project_context=payload.project,
        )
        return RequirementsResponse(
            success=True,
            requirements=reqs,
            wizardSync={
                "property": {
                    "siteWidth": reqs.plot_width,
                    "siteLength": reqs.plot_depth,
                    "floors": reqs.number_of_floors,
                    "orientation": reqs.orientation,
                },
                "family": {
                    "rooms": reqs.room_counts,
                    "requirements": reqs.special_requirements,
                },
                "style": {
                    "architecturalStyle": reqs.architectural_style,
                },
            },
        )
    except Exception as exc:
        logger.error(f"Error extracting requirements: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extract architectural requirements")


@router.post("/generate-floorplan")
def generate_floorplans_ai(payload: GenerateFloorplanRequest):
    """
    Full End-to-End Architectural Pipeline:
      Prompt → Gemini NLU → HouseRequirements → RequirementValidator →
      FloorplanGenerator (5 Typologies) → GeometryValidator → SpatialEvaluator →
      ParetoRanker → VastuScorer → 2D CAD SVG Blueprints + 3D Scene Graph
    """
    try:
        result = orchestrator.generate_floorplans(
            prompt=payload.prompt,
            top_k=payload.topK,
            project_payload=payload.project,
        )
        return result
    except Exception as exc:
        logger.error(f"Error generating floorplans via AI orchestrator: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Floorplan generation pipeline encountered an error")


@router.post("/analyze-floorplan-image")
async def analyze_floorplan_image(request: Request):
    """
    Uploads a 2D floorplan drawing or sketch (JPG, PNG, WEBP) to be analyzed
    via Gemini Vision into structured rooms, doors, windows, and dimensions,
    and transformed into validated vector CAD geometry.
    Supports either multipart/form-data upload or JSON with base64 imageDataUrl.
    """
    try:
        content_type = request.headers.get("content-type", "")
        image_bytes: Optional[bytes] = None
        mime_type = "image/png"
        user_prompt: Optional[str] = None

        if "multipart/form-data" in content_type:
            form = await request.form()
            uploaded_file = form.get("file")
            if uploaded_file and hasattr(uploaded_file, "read"):
                image_bytes = await uploaded_file.read()
                mime_type = getattr(uploaded_file, "content_type", "image/png") or "image/png"
            user_prompt = form.get("prompt")
        else:
            # JSON payload
            try:
                payload = await request.json()
            except Exception:
                payload = {}
            user_prompt = payload.get("prompt")
            data_url = payload.get("imageDataUrl") or payload.get("image") or ""
            if "," in data_url:
                header, b64 = data_url.split(",", 1)
                image_bytes = base64.b64decode(b64)
                if "image/jpeg" in header:
                    mime_type = "image/jpeg"
                elif "image/webp" in header:
                    mime_type = "image/webp"
            elif data_url:
                image_bytes = base64.b64decode(data_url)

        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image file or imageDataUrl provided in request")

        result = orchestrator.analyze_floorplan_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            user_prompt=user_prompt,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error analyzing floorplan image: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Floorplan image analysis failed")


@router.post("/modify")
def modify_floorplan_ai(payload: ModifyFloorplanRequest):
    """
    Conversational Floorplan Modification Endpoint:
      Natural Language Instruction → Gemini DesignOperation Decomposition →
      Deterministic Local Room/Geometry Transformation → 12-Constraint Validation →
      Spatial Re-Evaluation → Updated 2D CAD SVG + 3D Scene
    """
    try:
        result = orchestrator.modify_floorplan(
            prompt=payload.prompt,
            candidate=payload.candidate,
            project_payload=payload.project,
        )
        return result
    except Exception as exc:
        logger.error(f"Error modifying floorplan: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Floorplan conversational modification failed")
