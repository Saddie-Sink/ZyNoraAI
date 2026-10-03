"""
ZYNORA AI — AI Orchestrator
============================
Central orchestration engine coordinating:
  1. Gemini NLU & Vision Interpretation Layer
  2. Pydantic Requirement Validation
  3. Adapters to ZyNoraAI Deterministic Architectural Geometry
  4. Multi-Archetype Candidate Generation & 6D Pareto Ranking
  5. 12-Point Geometry Validation & Auto-Correction
  6. 2D CAD SVG Blueprint Synthesis
  7. 3D Dollhouse Scene Graph Generation
  8. Conversational Design Modification Dispatcher
"""
import copy
import logging
from typing import Dict, Any, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.ai.gemini_provider import GeminiProvider
from backend.app.ai.schemas import (
    HouseRequirements,
    DesignOperation,
    DesignOperationResult,
    FloorplanImageAnalysis,
)
from backend.app.ml.floorplan_generator import FloorplanGenerator
from backend.app.ml.requirement_validator import RequirementValidator
from backend.app.ml.spatial_evaluator import SpatialEvaluator
from backend.app.ml.pareto_ranker import ParetoRanker
from backend.app.ml.vastu_scorer import VastuScorer
from backend.app.geometry.geometry_validator import GeometryValidator
from backend.app.geometry.scene_3d_builder import Scene3DBuilder
from backend.app.geometry.floorplan_svg_renderer import render_floorplan_to_svg

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Central AI interpretation and orchestration engine.
    Ensures Gemini interprets intent while ZyNoraAI's deterministic engines
    generate and validate all architectural geometry.
    """

    def __init__(self):
        self.provider = GeminiProvider()
        self.generator = FloorplanGenerator()
        self.req_validator = RequirementValidator()
        self.geom_validator = GeometryValidator()
        self.spatial_evaluator = SpatialEvaluator()
        self.pareto_ranker = ParetoRanker()
        self.vastu_scorer = VastuScorer()
        self.scene_builder = Scene3DBuilder()

    # ─── 1. Status & Diagnostics ──────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        capabilities = [
            "Natural-Language Architectural Requirement Understanding",
            "Deterministic Multi-Archetype Floorplan Synthesis (5 Archetypes → Top 3)",
            "12-Constraint Geometric Validation & Auto-Correction",
            "16-Zone Vastu Purusha Mandala Scoring",
            "Multi-Objective NSGA-II Pareto Optimization",
            "Vector 2D CAD SVG Blueprint Synthesis",
            "Structured3D Neural Extrusion & Interactive 3D Dollhouse Scene Graph",
            "Headless Blender 4.5 Photorealistic Architectural Perspectives",
        ]
        if self.provider.is_configured:
            capabilities.append("Google Gemini 3.8 / 2.5 Flash GenAI Extraction & Vision")

        return {
            "configured": self.provider.is_configured,
            "provider": f"Google Gemini SDK ({self.provider.model_name})" if self.provider.is_configured else "Local Neuro-Symbolic AI",
            "model": self.provider.model_name,
            "activeCapabilities": capabilities,
            "maxCandidates": settings.ZYNORA_MAX_CANDIDATES,
            "defaultUnit": settings.ZYNORA_DEFAULT_UNIT,
            "vastuEnabled": settings.ZYNORA_ENABLE_VASTU,
            "blenderEnabled": settings.ZYNORA_ENABLE_BLENDER,
        }

    # ─── 2. Requirement Extraction & Validation ───────────────────────────────
    def extract_requirements(
        self,
        prompt: str,
        project_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[HouseRequirements, Dict[str, Any]]:
        """
        Interprets natural language into structured HouseRequirements and runs
        deterministic pre-generation validation.
        """
        requirements = self.provider.extract_requirements(prompt, project_context)
        validation_payload = self._convert_house_requirements_to_validator_format(requirements)
        validation_report = self.req_validator.validate(validation_payload)
        return requirements, validation_report

    # ─── 3. Multi-Candidate Floorplan Generation ──────────────────────────────
    def generate_floorplans(
        self,
        prompt: Optional[str] = None,
        top_k: int = 3,
        project_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end architectural pipeline:
          Prompt → Gemini → HouseRequirements → Validator → FloorplanGenerator →
          5 Typologies → GeometryValidator → ParetoRanker → Top K Candidates →
          2D CAD SVG Blueprints + 3D Scene Graph
        """
        k = max(1, min(settings.ZYNORA_MAX_CANDIDATES, top_k or 3))
        merged_project = dict(project_payload or {})
        if prompt:
            merged_project["nlPrompt"] = prompt
            merged_project["prompt"] = prompt

        # 1. Extract and validate structured requirements
        requirements, req_validation = self.extract_requirements(
            prompt=merged_project.get("nlPrompt", ""),
            project_context=merged_project,
        )

        # 2. Adapt HouseRequirements into the format FloorplanGenerator expects
        generator_payload = self._adapt_requirements_to_generator_payload(requirements, merged_project)
        generator_payload["topK"] = k

        # 3. Generate candidates using existing ZyNoraAI generator
        raw_candidates = self.generator.generate_candidates(generator_payload, top_k=k)

        # 4. Enhance each candidate with 2D SVG Blueprint & 3D Scene Graph
        enriched_candidates: List[Dict[str, Any]] = []
        for cand in raw_candidates:
            cand_copy = dict(cand)

            # Generate vector CAD SVG blueprint if not already present
            if not cand_copy.get("svgBlueprint"):
                cand_copy["svgBlueprint"] = render_floorplan_to_svg(cand_copy, floor_idx=0)

            # Generate 3D dollhouse scene graph
            if not cand_copy.get("scene3D"):
                cand_copy["scene3D"] = self.scene_builder.build_scene(cand_copy)

            # Standardize dimensions summary
            site_b = cand_copy.get("siteBoundary", {})
            cand_copy["dimensions"] = {
                "siteWidth": float(site_b.get("width", requirements.plot_width or 30.0)),
                "siteDepth": float(site_b.get("depth", requirements.plot_depth or 40.0)),
                "unit": requirements.units,
                "floors": requirements.number_of_floors,
                "builtUpArea": float(cand_copy.get("area", 2400.0)),
            }

            cand_copy["assumptions"] = list(requirements.assumptions)
            cand_copy["missingInformation"] = list(requirements.missing_information)
            enriched_candidates.append(cand_copy)

        best_cand = enriched_candidates[0] if enriched_candidates else {}

        return {
            "success": True,
            "requirements": requirements.model_dump(),
            "requirementValidation": req_validation,
            "candidates": enriched_candidates,
            "count": len(enriched_candidates),
            "bestCandidateId": best_cand.get("id"),
            "bestCandidateCode": best_cand.get("code"),
            "bestCandidateTitle": best_cand.get("title"),
            "selectionReasons": best_cand.get("selectionReasons", []),
        }

    # ─── 4. Conversational Editing ────────────────────────────────────────────
    def modify_floorplan(
        self,
        prompt: str,
        candidate: Dict[str, Any],
        project_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Applies conversational natural-language instructions deterministically:
          1. Gemini translates prompt to DesignOperation list.
          2. Operations applied to room dimensions, adjacencies, orientation, lighting.
          3. GeometryValidator validates & re-aligns geometry, resolving overlaps.
          4. Evaluators re-score Vastu, efficiency, and aesthetics.
          5. SVG and 3D scenes regenerated.
        """
        clean_prompt = (prompt or "").strip()
        op_result = self.provider.interpret_design_operation(clean_prompt, candidate)

        modified_cand = copy.deepcopy(candidate)
        rooms: List[Dict[str, Any]] = modified_cand.get("rooms", [])
        floors_geom: List[Dict[str, Any]] = modified_cand.get("floorsGeometry", [])
        site_b: Dict[str, Any] = modified_cand.get("siteBoundary", {"width": 30.0, "depth": 40.0})

        applied_operations: List[str] = []

        for op in op_result.operations:
            op_type = op.operation
            target = op.target.lower().strip()
            params = op.parameters

            # A. RESIZE_ROOM
            if op_type == "RESIZE_ROOM":
                matched_room = self._find_room_by_target(rooms, target)
                if matched_room:
                    old_w = float(matched_room.get("width", 10.0))
                    old_h = float(matched_room.get("height", 10.0))
                    if "width" in params and "height" in params:
                        new_w = float(params["width"])
                        new_h = float(params["height"])
                    elif "scale_factor" in params:
                        sf = float(params["scale_factor"])
                        new_w = round(old_w * sf, 2)
                        new_h = round(old_h * sf, 2)
                    else:
                        new_w, new_h = old_w * 1.15, old_h * 1.15

                    matched_room["width"] = new_w
                    matched_room["height"] = new_h
                    matched_room["area"] = round(new_w * new_h)
                    applied_operations.append(f"Resized {matched_room.get('name')} to {new_w:g}' × {new_h:g}' ({matched_room['area']} sq ft)")

            # B. MOVE_ROOM
            elif op_type == "MOVE_ROOM":
                matched_room = self._find_room_by_target(rooms, target)
                if matched_room:
                    adj_target = (params.get("adjacent_to") or ["living"])[0].lower()
                    target_neighbor = self._find_room_by_target(rooms, adj_target)
                    if target_neighbor and target_neighbor != matched_room:
                        # Place adjacent to target neighbor
                        matched_room["x"] = round(float(target_neighbor.get("x", 0.0)) + float(target_neighbor.get("width", 10.0)), 2)
                        matched_room["y"] = float(target_neighbor.get("y", 0.0))
                        applied_operations.append(f"Positioned {matched_room.get('name')} adjacent to {target_neighbor.get('name')}")

            # C. ADD_ROOM
            elif op_type in ("ADD_ROOM", "ADD_COURTYARD", "ADD_BALCONY", "ADD_TERRACE", "ADD_PARKING"):
                r_type = params.get("type", target)
                r_name = target.replace("_", " ").title()
                new_room = {
                    "name": r_name,
                    "type": r_type,
                    "width": float(params.get("width", 10.0)),
                    "height": float(params.get("height", 10.0)),
                    "area": float(params.get("area", 100.0)),
                    "x": 2.0,
                    "y": 2.0,
                    "floor": int(params.get("floor_level", 0)),
                }
                rooms.append(new_room)
                applied_operations.append(f"Added {r_name} ({new_room['width']:g}' × {new_room['height']:g}')")

            # D. REMOVE_ROOM
            elif op_type == "REMOVE_ROOM":
                matched_room = self._find_room_by_target(rooms, target)
                if matched_room:
                    rooms.remove(matched_room)
                    applied_operations.append(f"Removed {matched_room.get('name')}")

            # E. CHANGE_ORIENTATION
            elif op_type == "CHANGE_ORIENTATION":
                new_dir = str(params.get("direction", "North")).title()
                site_b["entranceDirection"] = new_dir
                modified_cand["orientation"] = new_dir
                applied_operations.append(f"Rotated entrance threshold to {new_dir}-Facing")

            # F. CHANGE_LIGHTING
            elif op_type == "CHANGE_LIGHTING":
                time_of_day = str(params.get("time_of_day", "sunset")).lower()
                modified_cand["timeOfDay3D"] = time_of_day
                applied_operations.append(f"Adjusted 3D scene lighting to {time_of_day.replace('_', ' ').title()}")

            # G. OPTIMIZE_VASTU
            elif op_type == "OPTIMIZE_VASTU":
                # Nudge Vastu zones
                for r in rooms:
                    rt = r.get("type", "")
                    if rt == "pooja":
                        r["vastu_zone"] = "NE"
                    elif rt == "kitchen":
                        r["vastu_zone"] = "SE"
                    elif rt == "bedroom" and "master" in r.get("name", "").lower():
                        r["vastu_zone"] = "SW"
                applied_operations.append("Optimized sacred Vastu Purusha Mandala room alignments (NE Pooja, SE Kitchen, SW Master)")

        # Sync rooms back into floor geometry
        if floors_geom:
            floors_geom[0]["rooms"] = [r for r in rooms if r.get("floor", 0) == 0]
        modified_cand["rooms"] = rooms

        # Run 12-point geometry validation and auto-correction
        raw_floorplan_geom = {
            "siteBoundary": site_b,
            "buildingBoundary": modified_cand.get("buildingBoundary", {"x": 2, "y": 3, "width": 26, "depth": 35}),
            "floorsGeometry": floors_geom,
            "rooms": rooms,
        }
        structured_reqs = modified_cand.get("structuredRequirements", {})
        corrected_geom, geom_report = self.geom_validator.validate_and_correct(
            raw_floorplan_geom, structured_reqs
        )

        modified_cand["rooms"] = corrected_geom["rooms"]
        modified_cand["floorsGeometry"] = corrected_geom["floorsGeometry"]
        modified_cand["geometryValidation"] = geom_report
        modified_cand["qualityChecklist"] = geom_report.get("qualityChecklist", [])

        # Re-score Vastu & efficiency
        new_vastu_score = self.vastu_scorer.score(
            orientation=modified_cand.get("orientation", "East"),
            typology=modified_cand.get("floorplanSvgType", "balanced"),
            rooms=modified_cand["rooms"],
        )
        modified_cand["vastuScore"] = new_vastu_score
        modified_cand["area"] = sum(float(r.get("area", 0)) for r in modified_cand["rooms"])

        # Re-render 2D SVG & 3D Scene
        modified_cand["svgBlueprint"] = render_floorplan_to_svg(modified_cand, floor_idx=0)
        modified_cand["scene3D"] = self.scene_builder.build_scene(modified_cand)

        return {
            "success": True,
            "summary": op_result.summary,
            "appliedOperations": applied_operations or [op_result.summary],
            "candidate": modified_cand,
            "geometryValidation": geom_report,
        }

    # ─── 5. Floorplan Image Understanding ─────────────────────────────────────
    def analyze_floorplan_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes an uploaded floorplan image through Gemini Vision, normalizes
        the observations, and maps them into a full deterministic ZyNoraAI layout.
        """
        analysis: FloorplanImageAnalysis = self.provider.analyze_floorplan_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            user_prompt=user_prompt,
        )

        # Convert detected image rooms into standard HouseRequirements
        detected_rooms_dict: Dict[str, int] = {}
        for r in analysis.rooms:
            rtype = r.type
            detected_rooms_dict[rtype] = detected_rooms_dict.get(rtype, 0) + 1

        prompt_summary = (
            f"Synthesize residential floorplan from uploaded image. "
            f"Rooms detected: {', '.join(f'{k}: {v}' for k, v in detected_rooms_dict.items())}. "
            f"Orientation: {analysis.detected_orientation or 'East'}."
        )

        # Generate candidates based on image extraction
        synth_result = self.generate_floorplans(prompt=prompt_summary, top_k=3)

        return {
            "success": True,
            "imageAnalysis": analysis.model_dump(),
            "detectedRooms": [r.model_dump() for r in analysis.rooms],
            "estimatedOrientation": analysis.detected_orientation,
            "dimensionsVisible": analysis.dimensions_visible,
            "unreadableElements": analysis.unreadable_elements,
            "candidates": synth_result.get("candidates", []),
            "bestCandidateId": synth_result.get("bestCandidateId"),
        }

    # ─── Helper Methods ───────────────────────────────────────────────────────
    def _find_room_by_target(self, rooms: List[Dict[str, Any]], target: str) -> Optional[Dict[str, Any]]:
        target_norm = target.replace("_", " ").lower()
        for r in rooms:
            r_name = str(r.get("name", "")).lower()
            r_type = str(r.get("type", "")).lower()
            if target_norm in r_name or target_norm == r_type or target in r_type:
                return r
        return None

    def _convert_house_requirements_to_validator_format(
        self,
        reqs: HouseRequirements,
    ) -> Dict[str, Any]:
        return {
            "site": {
                "width": reqs.plot_width or 30.0,
                "depth": reqs.plot_depth or 40.0,
                "area": (reqs.plot_width or 30.0) * (reqs.plot_depth or 40.0),
                "shape": "rectangular",
                "unit": reqs.units,
                "entranceDirection": reqs.orientation,
            },
            "floors": reqs.number_of_floors,
            "targetBuiltUpArea": ((reqs.plot_width or 30.0) * (reqs.plot_depth or 40.0) * 0.75 * reqs.number_of_floors),
            "requiredRooms": reqs.room_counts,
            "parking": {"required": reqs.parking.required, "cars": reqs.parking.car_count},
            "staircase": {"required": reqs.staircase.required or reqs.number_of_floors >= 2},
            "specialRequirements": reqs.special_requirements,
            "mandatoryRequirements": [],
            "optionalRequirements": [],
        }

    def _adapt_requirements_to_generator_payload(
        self,
        reqs: HouseRequirements,
        original_project: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Converts HouseRequirements to FloorplanGenerator input dictionary."""
        site_w = float(reqs.plot_width or 30.0)
        site_d = float(reqs.plot_depth or 40.0)
        floors = int(reqs.number_of_floors or 1)
        built_up = round(site_w * site_d * 0.75 * floors)

        adapted = copy.deepcopy(original_project)
        adapted["property"] = {
            "siteWidth": site_w,
            "siteLength": site_d,
            "floors": floors,
            "builtUpArea": built_up,
            "plotShape": "Rectangle",
            "orientation": reqs.orientation,
        }
        adapted["location"] = {
            "orientation": reqs.orientation,
        }
        adapted["family"] = {
            "rooms": {
                "bedrooms": reqs.room_counts.get("bedrooms", 3),
                "bathrooms": reqs.room_counts.get("bathrooms", 2),
                "livingRoom": reqs.room_counts.get("living", 1),
                "dining": reqs.room_counts.get("dining", 1),
                "kitchen": reqs.room_counts.get("kitchen", 1),
                "pooja": reqs.room_counts.get("pooja", 1),
                "parking": reqs.parking.car_count if reqs.parking.required else 0,
                "study": reqs.room_counts.get("study", 0),
                "utility": reqs.room_counts.get("utility", 1),
                "balcony": reqs.room_counts.get("balcony", 1),
            },
            "requirements": reqs.special_requirements,
        }
        adapted["style"] = {
            "architecturalStyle": reqs.architectural_style,
        }
        return adapted
