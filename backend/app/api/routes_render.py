"""
Approach 3 ArchViz & Gemini 3D Rendering API Router
"""
import os
import base64
import json
import urllib.request
from fastapi import APIRouter
from typing import Dict, Any
from backend.app.render.archviz_pipeline import ArchVizPipeline

router = APIRouter(prefix="/render", tags=["render"])
archviz = ArchVizPipeline()

GEMINI_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"


@router.post("/gemini-3d")
def generate_gemini_3d(payload: Dict[str, Any]):
    """
    Generate a 3D Floor Plan Cutaway render using Google Gemini 3.1 Flash Image
    (`gemini-3.1-flash-image`) via the official Gemini Interactions API.
    """
    api_key = (
        payload.get("apiKey")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    ).strip()

    if not api_key:
        return {
            "success": False,
            "error": "GEMINI_API_KEY not configured on backend",
        }

    prompt = payload.get("prompt", "Photorealistic 3D floor plan cutaway")
    image_data_url = payload.get("imageDataUrl")
    previous_id = payload.get("previousInteractionId")
    model = payload.get("model", "gemini-3.1-flash-image")

    # Try official google-genai SDK >= 2.3.0 if installed, otherwise direct Interactions REST
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        inputs = [
            {
                "type": "text",
                "text": f"Convert this 2D architectural floor plan into a high-resolution 3D floor plan cutaway visualization. {prompt}",
            }
        ]
        if image_data_url and isinstance(image_data_url, str) and "," in image_data_url:
            header, b64_data = image_data_url.split(",", 1)
            mime_type = "image/png"
            if "image/jpeg" in header:
                mime_type = "image/jpeg"
            elif "image/webp" in header:
                mime_type = "image/webp"
            inputs.append(
                {
                    "type": "image",
                    "data": b64_data,
                    "mime_type": mime_type,
                }
            )

        kwargs: Dict[str, Any] = {
            "model": model,
            "input": inputs,
            "response_format": {
                "type": "image",
                "aspect_ratio": "4:3",
                "image_size": "1K",
            },
        }
        if previous_id:
            kwargs["previous_interaction_id"] = previous_id

        interaction = client.interactions.create(**kwargs)
        out_img = getattr(interaction, "output_image", None)
        if out_img and getattr(out_img, "data", None):
            mime = getattr(out_img, "mime_type", "image/png") or "image/png"
            return {
                "success": True,
                "data": {
                    "imageUrl": f"data:{mime};base64,{out_img.data}",
                    "interactionId": getattr(interaction, "id", None),
                    "provider": "Gemini 3.1 Flash Image (Backend SDK)",
                },
            }
    except Exception:
        pass

    # Direct REST call to v1beta/interactions
    try:
        inputs = [
            {
                "type": "text",
                "text": f"Convert this 2D architectural floor plan into a high-resolution 3D floor plan cutaway visualization. {prompt}",
            }
        ]
        if image_data_url and isinstance(image_data_url, str) and "," in image_data_url:
            header, b64_data = image_data_url.split(",", 1)
            mime_type = "image/png"
            if "image/jpeg" in header:
                mime_type = "image/jpeg"
            elif "image/webp" in header:
                mime_type = "image/webp"
            inputs.append(
                {
                    "type": "image",
                    "mime_type": mime_type,
                    "data": b64_data,
                }
            )

        body: Dict[str, Any] = {
            "model": model,
            "input": inputs,
            "response_format": {
                "type": "image",
                "aspect_ratio": "4:3",
                "image_size": "1K",
            },
        }
        if previous_id:
            body["previous_interaction_id"] = previous_id

        req = urllib.request.Request(
            GEMINI_INTERACTIONS_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))

        out_img = resp_data.get("output_image")
        if out_img and out_img.get("data"):
            mime = out_img.get("mime_type", "image/png")
            return {
                "success": True,
                "data": {
                    "imageUrl": f"data:{mime};base64,{out_img['data']}",
                    "interactionId": resp_data.get("id"),
                    "provider": "Gemini 3.1 Flash Image",
                },
            }

        for step in reversed(resp_data.get("steps", [])):
            if step.get("type") == "model_output":
                for part in reversed(step.get("content", [])):
                    if part.get("data") and (
                        part.get("type") == "image"
                        or str(part.get("mime_type", "")).startswith("image/")
                    ):
                        mime = part.get("mime_type", "image/png")
                        return {
                            "success": True,
                            "data": {
                                "imageUrl": f"data:{mime};base64,{part['data']}",
                                "interactionId": resp_data.get("id"),
                                "provider": "Gemini 3.1 Flash Image",
                            },
                        }
        return {"success": False, "error": "No image part returned from Gemini"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.post("/views")
def generate_views(payload: Dict[str, Any]):
    views = archviz.generate_all_views(payload)
    return {
        "success": True,
        "data": {
            "renderJobId": f"job-archviz-{payload.get('id', 'cand-a')}",
            "status": "COMPLETED",
            "blenderDetected": archviz.blender_bin is not None,
            "views": views,
            "blendFile": "/renders/zynora_house.blend"
        }
    }

@router.post("/blender")
def trigger_blender_render(payload: Dict[str, Any]):
    """
    Triggers Blender 4.5 headless architectural generation and rendering
    for 5 exterior views matching the user's floor plan specifications.
    """
    house_w = float(payload.get("houseWidth", 30.0))
    house_d = float(payload.get("houseDepth", 19.0))
    ground_h = float(payload.get("groundHeight", 3.4))
    upper_h = float(payload.get("upperHeight", 3.2))

    success = archviz.render_with_blender(
        house_w=house_w,
        house_d=house_d,
        ground_h=ground_h,
        upper_h=upper_h
    )

    views = archviz.generate_all_views(payload)
    return {
        "success": success,
        "data": {
            "status": "COMPLETED" if success else "FALLBACK",
            "blenderDetected": archviz.blender_bin is not None,
            "blenderBin": archviz.blender_bin,
            "parameters": {
                "houseWidth": house_w,
                "houseDepth": house_d,
                "groundHeight": ground_h,
                "upperHeight": upper_h,
            },
            "views": views,
            "blendFile": "/renders/zynora_house.blend"
        }
    }

@router.get("/{render_id}")
def get_render_status(render_id: str):
    views = archviz.generate_all_views({"id": "cand-a"})
    return {
        "success": True,
        "data": {
            "renderJobId": render_id,
            "status": "COMPLETED",
            "blenderDetected": archviz.blender_bin is not None,
            "blenderBin": archviz.blender_bin,
            "views": views,
            "blendFile": "/renders/zynora_house.blend"
        }
    }
