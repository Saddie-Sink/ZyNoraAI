"""
ZYNORA AI — Production AI Architectural Pipeline Unit Tests
===========================================================
Comprehensive unit and integration test suite covering:
  1. Gemini provider initialization without API key
  2. Structured HouseRequirements validation
  3. Natural-language requirement conversion
  4. Candidate generation integration (Top 3 candidates)
  5. Geometry validation
  6. DesignOperation validation
  7. Conversational modification
  8. Floorplan image schema validation
  9. 3D scene generation
 10. API endpoint smoke tests
"""
import os
import unittest
import base64
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.ai.gemini_provider import GeminiProvider
from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.ai.schemas import (
    HouseRequirements,
    RoomItem,
    DesignOperation,
    DesignOperationResult,
    FloorplanImageAnalysis,
    DetectedImageRoom,
)
from backend.app.geometry.geometry_validator import GeometryValidator
from backend.app.geometry.scene_3d_builder import Scene3DBuilder
from backend.app.geometry.floorplan_svg_renderer import render_floorplan_to_svg


class TestAIPipeline(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.orchestrator = AIOrchestrator()
        self.sample_prompt = (
            "Design a 3 BHK modern East-facing residential house on a 30 by 40 feet plot "
            "with a spacious living room, modular kitchen, pooja room, and 2 bathrooms."
        )

    # ─── 1. Gemini Provider Init Without Key ─────────────────────────────────
    def test_gemini_provider_init_without_key(self):
        provider = GeminiProvider(api_key="")
        self.assertFalse(provider.is_configured)
        self.assertIn("gemini", provider.model_name.lower())

        # Test fallback works without error
        fallback_reqs = provider.extract_requirements(self.sample_prompt)
        self.assertIsInstance(fallback_reqs, HouseRequirements)
        self.assertEqual(fallback_reqs.plot_width, 30.0)
        self.assertEqual(fallback_reqs.plot_depth, 40.0)
        self.assertEqual(fallback_reqs.orientation, "East")

    # ─── 2. Structured HouseRequirements Validation ──────────────────────────
    def test_structured_house_requirements_validation(self):
        reqs = HouseRequirements(
            project_name="Coastal Villa",
            plot_width=40.0,
            plot_depth=60.0,
            units="ft",
            orientation="North",
            number_of_floors=2,
            rooms=[
                RoomItem(name="Living Hall", type="living", count=1, floor_level=0),
                RoomItem(name="Master Bedroom", type="master_bedroom", count=1, floor_level=0, en_suite_bathroom=True),
                RoomItem(name="Kitchen", type="kitchen", count=1, floor_level=0, vastu_zone_preference="SE"),
            ],
            room_counts={"bedrooms": 3, "bathrooms": 2, "living": 1, "kitchen": 1},
            architectural_style="Modern Minimalist",
            assumptions=["Assumed 2 covered parking slots"],
            missing_information=[],
        )
        self.assertEqual(reqs.plot_width, 40.0)
        self.assertEqual(reqs.plot_depth, 60.0)
        self.assertEqual(reqs.number_of_floors, 2)
        self.assertEqual(len(reqs.rooms), 3)

        # Serializes cleanly to dict
        dumped = reqs.model_dump()
        self.assertIn("rooms", dumped)
        self.assertIn("design_3d", dumped)
        self.assertEqual(dumped["design_3d"]["render_style"], "photorealistic")

    # ─── 3. Natural-Language Requirement Conversion ───────────────────────────
    def test_natural_language_requirement_conversion(self):
        reqs, validation = self.orchestrator.extract_requirements(self.sample_prompt)
        self.assertIsInstance(reqs, HouseRequirements)
        self.assertEqual(reqs.plot_width, 30.0)
        self.assertEqual(reqs.plot_depth, 40.0)
        self.assertEqual(reqs.orientation, "East")
        self.assertEqual(reqs.room_counts.get("bedrooms"), 3)
        self.assertEqual(reqs.room_counts.get("bathrooms"), 2)
        self.assertTrue(validation.get("isValid", True))

    # ─── 4. Candidate Generation Integration (Top 3 Candidates) ──────────────
    def test_candidate_generation_integration(self):
        result = self.orchestrator.generate_floorplans(self.sample_prompt, top_k=3)
        self.assertTrue(result["success"])
        candidates = result["candidates"]
        self.assertEqual(len(candidates), 3)
        self.assertEqual(result["count"], 3)

        for cand in candidates:
            self.assertIn("id", cand)
            self.assertIn("title", cand)
            self.assertIn("rooms", cand)
            self.assertIn("dimensions", cand)
            self.assertIn("geometryValidation", cand)
            self.assertIn("qualityScore", cand)
            self.assertIn("vastuScore", cand)
            self.assertIn("efficiency", cand)
            self.assertIn("svgBlueprint", cand)
            self.assertIn("scene3D", cand)
            self.assertTrue(cand["svgBlueprint"].startswith("<svg"))

        # Best candidate crowned rank #1
        best = candidates[0]
        self.assertEqual(best.get("rank"), 1)
        self.assertTrue(best.get("isTopRank"))
        self.assertTrue(best.get("isBestFloorplan"))

    # ─── 5. Geometry Validation ──────────────────────────────────────────────
    def test_geometry_validation(self):
        validator = GeometryValidator()
        floorplan_geom = {
            "siteBoundary": {"width": 30.0, "depth": 40.0},
            "buildingBoundary": {"x": 2.0, "y": 3.0, "width": 26.0, "depth": 35.0},
            "floorsGeometry": [
                {
                    "floor": 0,
                    "rooms": [
                        {"id": "r1", "name": "Drawing Room", "type": "living", "zone": "public", "x": 2.0, "y": 3.0, "width": 14.0, "height": 16.0, "area": 224},
                        {"id": "r2", "name": "Kitchen", "type": "kitchen", "zone": "service", "x": 16.0, "y": 3.0, "width": 12.0, "height": 12.0, "area": 144},
                    ],
                    "walls": [],
                    "doors": [],
                    "windows": [],
                }
            ],
            "rooms": [
                {"id": "r1", "name": "Drawing Room", "type": "living", "zone": "public", "x": 2.0, "y": 3.0, "width": 14.0, "height": 16.0, "area": 224},
                {"id": "r2", "name": "Kitchen", "type": "kitchen", "zone": "service", "x": 16.0, "y": 3.0, "width": 12.0, "height": 12.0, "area": 144},
            ],
        }
        corrected_geom, report = validator.validate_and_correct(floorplan_geom, {})
        self.assertTrue(report["isValid"])
        self.assertIn("qualityChecklist", report)
        self.assertGreaterEqual(len(report["qualityChecklist"]), 8)

    # ─── 6. DesignOperation Validation ───────────────────────────────────────
    def test_design_operation_validation(self):
        op = DesignOperation(
            operation="RESIZE_ROOM",
            target="master_bedroom",
            parameters={"width": 14.0, "height": 16.0, "unit": "ft"},
        )
        self.assertEqual(op.operation, "RESIZE_ROOM")
        self.assertEqual(op.target, "master_bedroom")
        self.assertEqual(op.parameters["width"], 14.0)

        res = DesignOperationResult(
            operations=[op],
            summary="Resized master bedroom to 14 by 16 feet",
            assumptions=["Preserved en-suite bathroom placement"],
        )
        self.assertEqual(len(res.operations), 1)

    # ─── 7. Conversational Modification ──────────────────────────────────────
    def test_conversational_modification(self):
        gen_res = self.orchestrator.generate_floorplans(self.sample_prompt, top_k=1)
        initial_cand = gen_res["candidates"][0]

        mod_res = self.orchestrator.modify_floorplan(
            prompt="Make master bedroom 16 by 18 feet and adjust 3D lighting to sunset",
            candidate=initial_cand,
        )
        self.assertTrue(mod_res["success"])
        modified_cand = mod_res["candidate"]
        self.assertIn("appliedOperations", mod_res)

        # Verify master bedroom was resized
        master_r = next((r for r in modified_cand["rooms"] if "master" in r.get("name", "").lower()), None)
        self.assertIsNotNone(master_r)
        self.assertGreaterEqual(float(master_r["width"]), 15.0)

        # Verify 3D lighting was adjusted
        self.assertEqual(modified_cand.get("timeOfDay3D"), "sunset")

        # Verify geometry was validated after modification
        self.assertIn("geometryValidation", mod_res)

    # ─── 8. Floorplan Image Schema Validation ─────────────────────────────────
    def test_floorplan_image_schema_validation(self):
        analysis = FloorplanImageAnalysis(
            rooms=[
                DetectedImageRoom(name="Master Bed", type="bedroom", dimensions_text="14' x 16'"),
                DetectedImageRoom(name="Drawing Hall", type="living", dimensions_text="18' x 20'"),
            ],
            walls_detected=True,
            doors_detected=True,
            windows_detected=True,
            dimensions_visible=True,
            unreadable_elements=[],
            notes_and_assumptions=["Verified crisp CAD linework"],
        )
        self.assertEqual(len(analysis.rooms), 2)
        self.assertTrue(analysis.dimensions_visible)

        # Test image analyzer fallback with dummy 1x1 PNG bytes
        dummy_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
        img_res = self.orchestrator.analyze_floorplan_image(dummy_png, mime_type="image/png")
        self.assertTrue(img_res["success"])
        self.assertIn("imageAnalysis", img_res)
        self.assertGreaterEqual(len(img_res["candidates"]), 1)

    # ─── 9. 3D Scene Generation ───────────────────────────────────────────────
    def test_3d_scene_generation(self):
        gen_res = self.orchestrator.generate_floorplans(self.sample_prompt, top_k=1)
        cand = gen_res["candidates"][0]

        builder = Scene3DBuilder()
        scene = builder.build_scene(cand, cutaway_height=1.8)

        self.assertIn("rooms", scene)
        self.assertIn("walls", scene)
        self.assertIn("furniture", scene)
        self.assertIn("cameraPresets", scene)
        self.assertIn("lighting", scene)
        self.assertGreater(len(scene["rooms"]), 0)
        self.assertGreater(len(scene["cameraPresets"]), 0)

    # ─── 10. API Endpoint Smoke Tests ─────────────────────────────────────────
    def test_api_endpoints_smoke(self):
        # 1. GET /api/ai/status
        status_resp = self.client.get("/api/ai/status")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertIn("configured", status_data)
        self.assertIn("activeCapabilities", status_data)
        # Ensure API key is NEVER exposed in status
        self.assertNotIn("apiKey", status_data)
        self.assertNotIn("api_key", status_data)

        # 2. POST /api/ai/requirements
        req_resp = self.client.post("/api/ai/requirements", json={"prompt": self.sample_prompt})
        self.assertEqual(req_resp.status_code, 200)
        self.assertTrue(req_resp.json()["success"])
        self.assertIn("requirements", req_resp.json())

        # 3. POST /api/ai/generate-floorplan
        gen_resp = self.client.post("/api/ai/generate-floorplan", json={"prompt": self.sample_prompt, "topK": 3})
        self.assertEqual(gen_resp.status_code, 200)
        gen_data = gen_resp.json()
        self.assertTrue(gen_data["success"])
        self.assertEqual(len(gen_data["candidates"]), 3)

        # 4. POST /api/ai/modify
        first_cand = gen_data["candidates"][0]
        mod_resp = self.client.post(
            "/api/ai/modify",
            json={"prompt": "Make kitchen larger with sunset lighting", "candidate": first_cand},
        )
        self.assertEqual(mod_resp.status_code, 200)
        self.assertTrue(mod_resp.json()["success"])

        # 5. POST /api/ai/analyze-floorplan-image (via base64 json payload)
        dummy_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        img_resp = self.client.post(
            "/api/ai/analyze-floorplan-image",
            json={"imageDataUrl": dummy_b64, "prompt": "Analyze uploaded 2BHK layout"},
        )
        self.assertEqual(img_resp.status_code, 200)
        self.assertTrue(img_resp.json()["success"])


if __name__ == "__main__":
    unittest.main()
