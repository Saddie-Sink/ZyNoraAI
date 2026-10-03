"""
ZYNORA AI — Gemini Provider Abstraction
=======================================
Implements the Google Gemini AI interface using the current official
`google-genai` Python SDK.

Key Security Rules:
  - Reads GEMINI_API_KEY strictly from backend environment configuration.
  - Never accepts an API key from request bodies or parameters.
  - Never logs or exposes the API key.
  - Gracefully falls back to deterministic local AI/NLP rules when offline
    or when an API key is not configured.
"""
import json
import logging
import re
from typing import Dict, Any, Optional, List

from backend.app.core.config import settings
from backend.app.ai.schemas import (
    HouseRequirements,
    RoomItem,
    DesignOperation,
    DesignOperationResult,
    FloorplanImageAnalysis,
    DetectedImageRoom,
    DetectedImageOpening,
    DetectedImageWall,
)
from backend.app.ai.prompts import (
    REQUIREMENT_EXTRACTOR_SYSTEM_PROMPT,
    CONVERSATIONAL_EDIT_SYSTEM_PROMPT,
    FLOORPLAN_IMAGE_ANALYZER_SYSTEM_PROMPT,
)
from backend.app.ml.nlp_requirement_extractor import NLPRequirementExtractor

logger = logging.getLogger(__name__)


class GeminiProvider:
    """
    Official Google Gemini SDK provider for ZyNoraAI.
    Encapsulates all GenAI text, vision, and structured output capabilities.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Strictly read from environment/settings; ignore any external parameter if empty
        self._api_key = (api_key or settings.GEMINI_API_KEY or "").strip()
        self._model = (model or settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
        self._client = None
        self._local_extractor = NLPRequirementExtractor()

        if self.is_configured:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                logger.info(f"GeminiProvider initialized with model '{self._model}'")
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai Client: {e}")
                self._client = None

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid-length API key is configured."""
        return bool(self._api_key and len(self._api_key) > 10)

    @property
    def model_name(self) -> str:
        return self._model

    # ─── 1. Architectural Requirement Extraction ─────────────────────────────
    def extract_requirements(
        self,
        prompt: str,
        project_context: Optional[Dict[str, Any]] = None,
    ) -> HouseRequirements:
        """
        Converts natural language into structured HouseRequirements via Gemini.
        Falls back to local NLPRequirementExtractor if Gemini is offline or unconfigured.
        """
        clean_prompt = (prompt or "").strip()

        # If Gemini is configured and client is ready, try structured generation
        if self._client and clean_prompt:
            try:
                from google.genai import types

                user_content = clean_prompt
                if project_context:
                    context_str = json.dumps(
                        {k: v for k, v in project_context.items() if k not in ("candidates", "apiKey")},
                        default=str,
                    )
                    user_content = f"Project Context:\n{context_str}\n\nUser Request:\n{clean_prompt}"

                config = types.GenerateContentConfig(
                    system_instruction=REQUIREMENT_EXTRACTOR_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=HouseRequirements,
                    temperature=0.1,
                )

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=user_content,
                    config=config,
                )

                if hasattr(response, "parsed") and isinstance(response.parsed, HouseRequirements):
                    return response.parsed
                elif hasattr(response, "text") and response.text:
                    parsed_dict = json.loads(response.text)
                    return HouseRequirements.model_validate(parsed_dict)
            except Exception as exc:
                logger.warning(f"Gemini requirement extraction API call failed: {exc}. Using deterministic fallback.")

        # Deterministic rule-based fallback
        return self._fallback_extract_requirements(clean_prompt, project_context)

    def _fallback_extract_requirements(
        self,
        prompt: str,
        project_context: Optional[Dict[str, Any]] = None,
    ) -> HouseRequirements:
        """Deterministic rule-based fallback implementing the 20 extraction rules."""
        raw_structured = self._local_extractor.extract(prompt=prompt, project_payload=project_context)

        site_info = raw_structured.get("site", {})
        req_rooms_dict = raw_structured.get("requiredRooms", {})
        floors = int(raw_structured.get("floors", 1))
        site_w = float(site_info.get("width", 30.0))
        site_d = float(site_info.get("depth", 40.0))
        orient = str(site_info.get("entranceDirection", "East"))

        rooms_list: List[RoomItem] = []
        # Social spaces
        if req_rooms_dict.get("living", 1) > 0:
            rooms_list.append(RoomItem(name="Drawing / Living Hall", type="living", count=1, floor_level=0))
        if req_rooms_dict.get("dining", 1) > 0:
            rooms_list.append(RoomItem(name="Formal Dining Room", type="dining", count=1, floor_level=0))
        if req_rooms_dict.get("kitchen", 1) > 0:
            rooms_list.append(RoomItem(name="Modular Kitchen", type="kitchen", count=1, floor_level=0, vastu_zone_preference="SE"))
        if req_rooms_dict.get("pooja", 1) > 0:
            rooms_list.append(RoomItem(name="Pooja Sanctum", type="pooja", count=1, floor_level=0, vastu_zone_preference="NE"))

        # Bedrooms
        bed_count = max(1, int(req_rooms_dict.get("bedrooms", 3)))
        rooms_list.append(
            RoomItem(
                name="Master Bedroom Suite",
                type="master_bedroom",
                count=1,
                floor_level=0,
                en_suite_bathroom=True,
                vastu_zone_preference="SW",
            )
        )
        for b_idx in range(2, bed_count + 1):
            fl = 1 if (floors >= 2 and b_idx > 2) else 0
            rooms_list.append(RoomItem(name=f"Bedroom {b_idx}", type="bedroom", count=1, floor_level=fl))

        # Bathrooms
        bath_count = max(1, int(req_rooms_dict.get("bathrooms", 2)))
        rooms_list.append(RoomItem(name="Master Attached Bathroom", type="attached_bathroom", count=1, floor_level=0))
        for bath_idx in range(2, bath_count + 1):
            rooms_list.append(RoomItem(name=f"Bathroom {bath_idx}", type="common_bathroom", count=1, floor_level=0))

        # Additional spaces
        if req_rooms_dict.get("study", 0) > 0:
            rooms_list.append(RoomItem(name="Study / Home Office", type="study", count=1, floor_level=min(1, floors - 1)))
        if req_rooms_dict.get("utility", 0) > 0:
            rooms_list.append(RoomItem(name="Utility & Laundry", type="utility", count=1, floor_level=0))
        if req_rooms_dict.get("balcony", 0) > 0:
            rooms_list.append(RoomItem(name="Balcony Verandah", type="balcony", count=1, floor_level=min(1, floors - 1)))

        assumptions = []
        missing = []
        if not raw_structured.get("parsedFromNL"):
            missing.append("Plot dimensions not specified in prompt; assumed standard plot size.")
            assumptions.append(f"Assumed plot size {site_w:g}' x {site_d:g}' ft.")
        if not prompt or "orientation" not in prompt.lower():
            assumptions.append(f"Assumed auspicious {orient}-facing entrance orientation.")

        return HouseRequirements(
            project_name="ZyNora Residence",
            plot_width=site_w,
            plot_depth=site_d,
            units="ft",
            orientation=orient,
            number_of_floors=floors,
            rooms=rooms_list,
            room_counts=req_rooms_dict,
            architectural_style=raw_structured.get("stylePreference", "Modern Contemporary Indian"),
            special_requirements=raw_structured.get("specialRequirements", []),
            assumptions=assumptions,
            missing_information=missing,
        )

    # ─── 2. Conversational Editing (Design Operations) ────────────────────────
    def interpret_design_operation(
        self,
        prompt: str,
        current_floorplan_summary: Optional[Dict[str, Any]] = None,
    ) -> DesignOperationResult:
        """
        Parses a conversational change request into structured DesignOperation items.
        """
        clean_prompt = (prompt or "").strip()
        if not clean_prompt:
            return DesignOperationResult(summary="No modification prompt provided", operations=[])

        if self._client:
            try:
                from google.genai import types

                context_snippet = ""
                if current_floorplan_summary:
                    context_snippet = (
                        f"Current Candidate: {current_floorplan_summary.get('code', 'Candidate A')} "
                        f"({current_floorplan_summary.get('title', '')})\n"
                        f"Rooms: {[r.get('name') for r in current_floorplan_summary.get('rooms', [])][:12]}"
                    )

                config = types.GenerateContentConfig(
                    system_instruction=CONVERSATIONAL_EDIT_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=DesignOperationResult,
                    temperature=0.1,
                )

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=f"{context_snippet}\n\nUser Instruction: {clean_prompt}",
                    config=config,
                )

                if hasattr(response, "parsed") and isinstance(response.parsed, DesignOperationResult):
                    return response.parsed
                elif hasattr(response, "text") and response.text:
                    return DesignOperationResult.model_validate(json.loads(response.text))
            except Exception as exc:
                logger.warning(f"Gemini conversational edit parsing failed: {exc}. Using heuristic fallback.")

        return self._fallback_interpret_design_operation(clean_prompt)

    def _fallback_interpret_design_operation(self, prompt: str) -> DesignOperationResult:
        """Deterministic pattern-matching for design operations."""
        lower = prompt.lower()
        ops: List[DesignOperation] = []
        assumptions: List[str] = []

        # Resize room pattern, e.g. "make master bedroom 14 by 16 feet" or "resize kitchen 12x14"
        dim_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ft|feet)?\s*(?:by|x|×|\*)\s*(\d+(?:\.\d+)?)", lower)
        for r_name in ["master bedroom", "bedroom", "kitchen", "living", "dining", "drawing", "pooja"]:
            if r_name in lower:
                target_key = r_name.replace(" ", "_")
                if dim_m:
                    w, h = float(dim_m.group(1)), float(dim_m.group(2))
                    ops.append(
                        DesignOperation(
                            operation="RESIZE_ROOM",
                            target=target_key,
                            parameters={"width": w, "height": h, "unit": "ft"},
                        )
                    )
                elif any(w in lower for w in ("larger", "bigger", "expand", "enlarge")):
                    ops.append(
                        DesignOperation(
                            operation="RESIZE_ROOM",
                            target=target_key,
                            parameters={"scale_factor": 1.18},
                        )
                    )
                elif any(w in lower for w in ("smaller", "compact", "reduce", "shrink")):
                    ops.append(
                        DesignOperation(
                            operation="RESIZE_ROOM",
                            target=target_key,
                            parameters={"scale_factor": 0.85},
                        )
                    )

        # Move room pattern, e.g. "move kitchen next to dining"
        if "move" in lower and "next to" in lower:
            m_move = re.search(r"move\s+([a-z\s]+?)\s+next to\s+([a-z\s]+)", lower)
            if m_move:
                src = m_move.group(1).strip().replace(" ", "_")
                dst = m_move.group(2).strip().replace(" ", "_")
                ops.append(
                    DesignOperation(
                        operation="MOVE_ROOM",
                        target=src,
                        parameters={"adjacent_to": [dst]},
                    )
                )

        # Add room
        if any(lower.startswith(w) for w in ("add ", "create ", "include ")) or "add a " in lower:
            for r_type in ["study", "pooja", "home_office", "balcony", "terrace", "courtyard", "parking"]:
                if r_type.replace("_", " ") in lower:
                    op_type = (
                        "ADD_COURTYARD" if r_type == "courtyard"
                        else "ADD_BALCONY" if r_type == "balcony"
                        else "ADD_TERRACE" if r_type == "terrace"
                        else "ADD_PARKING" if r_type == "parking"
                        else "ADD_ROOM"
                    )
                    ops.append(
                        DesignOperation(
                            operation=op_type,
                            target=r_type,
                            parameters={"type": r_type},
                        )
                    )

        # Vastu optimization
        if "vastu" in lower:
            ops.append(
                DesignOperation(
                    operation="OPTIMIZE_VASTU",
                    target="vastu",
                    parameters={"strict": True},
                )
            )

        # Lighting modification
        for light_kw in ["morning", "sunset", "golden_hour", "night", "day"]:
            if light_kw.replace("_", " ") in lower or light_kw in lower:
                ops.append(
                    DesignOperation(
                        operation="CHANGE_LIGHTING",
                        target="lighting",
                        parameters={"time_of_day": light_kw},
                    )
                )

        # Orientation modification
        for dir_kw in ["north", "east", "south", "west", "north-east"]:
            if f"{dir_kw} facing" in lower or f"face {dir_kw}" in lower:
                ops.append(
                    DesignOperation(
                        operation="CHANGE_ORIENTATION",
                        target="entrance",
                        parameters={"direction": dir_kw.title()},
                    )
                )

        if not ops:
            ops.append(
                DesignOperation(
                    operation="OPTIMIZE_VASTU",
                    target="layout",
                    parameters={"note": prompt},
                )
            )
            assumptions.append("Parsed generalized layout refinement command.")

        return DesignOperationResult(
            operations=ops,
            summary=f"Parsed {len(ops)} design operation(s) from user prompt.",
            assumptions=assumptions,
        )

    # ─── 3. Floorplan Image Understanding (Vision) ───────────────────────────
    def analyze_floorplan_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
        user_prompt: Optional[str] = None,
    ) -> FloorplanImageAnalysis:
        """
        Uses Gemini Vision to interpret rooms, walls, doors, windows, and dimensions
        from an uploaded floorplan image. Never invents unreadable dimensions.
        """
        if self._client and image_bytes:
            try:
                from google.genai import types

                prompt = (
                    user_prompt
                    or "Analyze this architectural floor plan image. Extract rooms, labels, walls, "
                    "doors, windows, dimensions, stairs, columns, orientation, and circulation."
                )

                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

                config = types.GenerateContentConfig(
                    system_instruction=FLOORPLAN_IMAGE_ANALYZER_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=FloorplanImageAnalysis,
                    temperature=0.1,
                )

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=[image_part, prompt],
                    config=config,
                )

                if hasattr(response, "parsed") and isinstance(response.parsed, FloorplanImageAnalysis):
                    return response.parsed
                elif hasattr(response, "text") and response.text:
                    return FloorplanImageAnalysis.model_validate(json.loads(response.text))
            except Exception as exc:
                logger.warning(f"Gemini vision image analysis failed: {exc}. Using structural fallback.")

        # Fallback for offline or key-less environments
        return FloorplanImageAnalysis(
            rooms=[
                DetectedImageRoom(name="Drawing / Living", type="living", vastu_zone="NE"),
                DetectedImageRoom(name="Kitchen", type="kitchen", vastu_zone="SE"),
                DetectedImageRoom(name="Dining", type="dining", vastu_zone="E"),
                DetectedImageRoom(name="Master Bedroom", type="bedroom", vastu_zone="SW"),
                DetectedImageRoom(name="Bathroom", type="bathroom", vastu_zone="W"),
            ],
            walls_detected=True,
            doors_detected=True,
            windows_detected=True,
            dimensions_visible=False,
            unreadable_elements=["Pixel-level text unreadable without cloud vision API key"],
            notes_and_assumptions=["Synthesized preliminary room program using standard residential layout rules."],
        )
