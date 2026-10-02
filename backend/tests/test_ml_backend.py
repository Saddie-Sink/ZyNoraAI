"""
ZYNORA-ML — Backend and ML Core Unit Tests
"""
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.spatial_graph import SpatialGraphBuilder
from backend.app.ml.floorplan_generator import FloorplanGenerator
from backend.app.ml.spatial_evaluator import SpatialEvaluator
from backend.app.ml.room_classifier import RoomClassifier
from backend.app.ml.pareto_ranker import ParetoRanker
from backend.app.geometry.parametric_3d import Parametric3DGenerator
from backend.app.render.archviz_pipeline import ArchVizPipeline

class TestMLBackend(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.sample_project = {
            "name": "Villa Aurelia",
            "projectType": "Villa",
            "property": {"builtUpArea": 3800, "floors": 2, "siteWidth": 60, "siteLength": 100},
            "family": {"rooms": {"bedrooms": 4, "bathrooms": 4, "livingRoom": 1, "kitchen": 1}},
            "location": {"orientation": "North"}
        }

    def test_health_check(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn(data["mlCoreStatus"]["status"], ("TRAINED", "FALLBACK"))

    def test_spatial_graph_builder(self):
        builder = SpatialGraphBuilder()
        G = builder.build_program_graph(self.sample_project["family"], self.sample_project["property"])
        self.assertGreater(G.number_of_nodes(), 5)
        self.assertIn("Living_Room", G.nodes)
        self.assertIn("Master_Suite", G.nodes)

    def test_floorplan_generator(self):
        gen = FloorplanGenerator()
        candidates = gen.generate_candidates(self.sample_project)
        self.assertEqual(len(candidates), 3)
        top_rank_count = sum(1 for c in candidates if c.get("isTopRank"))
        self.assertEqual(top_rank_count, 1)
        self.assertTrue(candidates[0]["isTopRank"])
        self.assertTrue(candidates[0].get("isBestFloorplan"))
        self.assertEqual(candidates[0].get("rank"), 1)
        self.assertGreater(len(candidates[0].get("selectionReasons", [])), 0)

    def test_requirement_driven_best_floorplan_adaptation(self):
        gen = FloorplanGenerator()
        # Scenario 1: Chettinad courtyard villa with Vastu & ventilation priorities
        courtyard_brief = {
            "property": {"builtUpArea": 3200, "floors": 2, "siteWidth": 50, "siteLength": 55, "plotShape": "Rectangle"},
            "family": {
                "adults": 4, "children": 2, "elderly": 1,
                "rooms": {"bedrooms": 4, "bathrooms": 4},
                "requirements": ["Vastu Shastra Compliance", "Cross Ventilation (Coastal Breeze)"]
            },
            "budget": {"priority": "Premium", "budgetRange": 24000000},
            "style": {"architecturalStyle": "Chettinad Contemporary", "customRequirements": "central courtyard"},
            "location": {"orientation": "East"}
        }
        cands_courtyard = gen.generate_candidates(courtyard_brief)
        self.assertEqual(len(cands_courtyard), 3)
        self.assertEqual(cands_courtyard[0]["id"], "cand-b")  # Central Atrium wins #1

        # Scenario 2: Economy budget on compact square plot
        economy_brief = {
            "property": {"builtUpArea": 1200, "floors": 1, "siteWidth": 30, "siteLength": 35, "plotShape": "Rectangle"},
            "family": {
                "adults": 2, "children": 1, "elderly": 0,
                "rooms": {"bedrooms": 2, "bathrooms": 2},
                "requirements": []
            },
            "budget": {"priority": "Economy", "budgetRange": 3500000},
            "style": {"architecturalStyle": "Modern Contemporary Indian"},
            "location": {"orientation": "North"}
        }
        cands_economy = gen.generate_candidates(economy_brief)
        self.assertEqual(len(cands_economy), 3)
        self.assertIn(cands_economy[0]["id"], ("cand-d", "cand-a"))  # Compact or Balanced wins #1

        # Scenario 3: L-Shape parcel with Elderly accessibility priority
        elder_l_brief = {
            "property": {"builtUpArea": 2600, "floors": 2, "siteWidth": 45, "siteLength": 55, "plotShape": "L-shape"},
            "family": {
                "adults": 2, "children": 1, "elderly": 2,
                "rooms": {"bedrooms": 3, "bathrooms": 3},
                "requirements": ["Elder-friendly ground floor access"]
            },
            "budget": {"priority": "Balanced", "budgetRange": 13000000},
            "style": {"architecturalStyle": "Modern Contemporary Indian"},
            "location": {"orientation": "North-West"}
        }
        cands_elder = gen.generate_candidates(elder_l_brief)
        self.assertEqual(len(cands_elder), 3)
        self.assertEqual(cands_elder[0]["id"], "cand-e")  # Segmented Privacy (L-shape) wins #1

    def test_spatial_evaluator(self):
        evaluator = SpatialEvaluator()
        score = evaluator.evaluate_space_efficiency([{"type": "living", "area": 500}], 3800)
        self.assertGreaterEqual(score, 70)
        daylight = evaluator.evaluate_daylighting_surrogate("North", "balanced")
        self.assertGreaterEqual(daylight, 70)

    def test_pareto_ranker(self):
        ranker = ParetoRanker()
        cands = [
            {"id": "c1", "code": "A", "title": "A", "efficiency": 95, "connectivity": 95, "naturalLight": 95, "ventilation": 90, "requirementMatch": 95},
            {"id": "c2", "code": "B", "title": "B", "efficiency": 80, "connectivity": 80, "naturalLight": 80, "ventilation": 80, "requirementMatch": 80}
        ]
        ranked = ranker.rank_candidates(cands)
        self.assertEqual(ranked[0]["candidateId"], "c1")
        self.assertTrue(ranked[0]["isTopRank"])

    def test_archviz_pipeline_approach_3(self):
        archviz = ArchVizPipeline()
        views = archviz.generate_all_views({"id": "cand-a"})
        self.assertEqual(len(views), 5)
        for v in views:
            self.assertTrue(
                v["imageDataUri"].startswith("data:image/") or v["imageDataUri"].startswith("/renders/")
            )
            self.assertIn("slot", v)

    def test_api_endpoints_end_to_end(self):
        # 1. Create project
        p_resp = self.client.post("/api/projects", json=self.sample_project)
        self.assertEqual(p_resp.status_code, 200)

        # 2. Generate floorplans (returns Top 3 and #1 Best Floorplan)
        fp_resp = self.client.post("/api/floorplans/generate", json=self.sample_project)
        self.assertEqual(fp_resp.status_code, 200)
        fp_data = fp_resp.json()["data"]
        cands = fp_data["candidates"]
        self.assertEqual(len(cands), 3)
        self.assertEqual(fp_data["count"], 3)
        self.assertEqual(fp_data["bestCandidateId"], cands[0]["id"])

        # 3. 3D Design
        d_resp = self.client.post("/api/design/generate", json={"candidateId": "cand-a", "area": 3800, "floors": 2})
        self.assertEqual(d_resp.status_code, 200)

        # 4. Render Views (Approach 3)
        r_resp = self.client.post("/api/render/views", json={"id": "cand-a"})
        self.assertEqual(r_resp.status_code, 200)
        self.assertEqual(len(r_resp.json()["data"]["views"]), 5)

if __name__ == "__main__":
    unittest.main()
