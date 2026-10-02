"""
ZYNORA-ML — 3D Architectural Design & Scene Synthesis Router
============================================================
Converts 2D topological floor plans into rich, physical 3D Dollhouse
scene graphs using:
  - Neural Extrusion (Structured3D 72K rooms)
  - Spatial Furniture Synthesizer (ML empirical priors)
  - PBR Material Shaders & Camera Presets
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from backend.app.geometry.parametric_3d import Parametric3DGenerator
from backend.app.geometry.scene_3d_builder import Scene3DBuilder
from backend.app.ml.indian_layout_engine import IndianLayoutEngine

router = APIRouter(prefix="/design", tags=["design"])
mesh_gen = Parametric3DGenerator()
scene_builder = Scene3DBuilder()
layout_engine = IndianLayoutEngine()


@router.post("/generate")
def generate_design(payload: Dict[str, Any]):
    cand_id = payload.get("candidateId", "cand-a")
    mesh = mesh_gen.generate_massing_mesh(cand_id, payload)
    return {
        "success": True,
        "data": mesh
    }


@router.post("/floorplan-to-3d")
def convert_floorplan_to_3d(payload: Dict[str, Any]):
    """
    Direct Floorplan to 3D Conversion Endpoint.
    Transforms any 2D floor plan layout into an architectural 3D Dollhouse scene.
    """
    cutaway_h = float(payload.get("cutawayHeight", 1.8))
    floorplan = payload.get("floorplan") or payload.get("candidate") or payload

    # If rooms don't have coordinates, pass through layout engine
    rooms = floorplan.get("rooms", [])
    has_coords = any(r.get("x") is not None for r in rooms)

    if not has_coords and rooms:
        shape = floorplan.get("layoutShape") or floorplan.get("floorplanSvgType", "rectangular")
        plot_w = float(floorplan.get("plot_w", 40.0) or 40.0)
        plot_h = float(floorplan.get("plot_h", 60.0) or 60.0)
        rooms_with_coords, plot_info = layout_engine.generate(shape, rooms, plot_w, plot_h)
        floorplan["rooms"] = rooms_with_coords
        floorplan["plotInfo"] = plot_info

    scene_3d = scene_builder.build_scene(floorplan, cutaway_height=cutaway_h)

    return {
        "success": True,
        "data": scene_3d
    }


@router.get("/sample-floorplans")
def get_sample_floorplans():
    """
    Returns 3 curated architectural floor plans ready for instant 3D conversion.
    """
    samples = [
        {
            "id": "sample-2bhk",
            "code": "2 BHK Coastal Modern",
            "title": "Compact 2 BHK Efficient Villa",
            "area": 1600,
            "bedrooms": 2,
            "bathrooms": 2,
            "layoutShape": "rectangular",
            "plot_w": 35.0,
            "plot_h": 45.0,
            "rooms": [
                {"name": "Drawing / Hall", "type": "living", "area": 310, "x": 0.5, "y": 0.5, "width": 16.0, "height": 19.4, "vastu_zone": "NE"},
                {"name": "Modular Kitchen", "type": "kitchen", "area": 140, "x": 17.5, "y": 0.5, "width": 12.0, "height": 11.6, "vastu_zone": "SE"},
                {"name": "Formal Dining", "type": "dining", "area": 160, "x": 17.5, "y": 12.5, "width": 12.0, "height": 13.3, "vastu_zone": "E"},
                {"name": "Master Bedroom", "type": "bedroom", "area": 260, "x": 0.5, "y": 21.0, "width": 16.0, "height": 16.2, "vastu_zone": "SW"},
                {"name": "Master Bathroom", "type": "bathroom", "area": 70, "x": 0.5, "y": 37.5, "width": 10.0, "height": 7.0, "vastu_zone": "SW"},
                {"name": "Guest Bedroom", "type": "bedroom", "area": 200, "x": 17.5, "y": 26.5, "width": 14.0, "height": 14.3, "vastu_zone": "NW"},
                {"name": "Common Bathroom", "type": "bathroom", "area": 55, "x": 17.5, "y": 41.0, "width": 9.0, "height": 6.1, "vastu_zone": "W"},
                {"name": "Pooja Room", "type": "pooja", "area": 45, "x": 11.0, "y": 37.5, "width": 5.5, "height": 8.0, "vastu_zone": "NE"},
                {"name": "Balcony / Verandah", "type": "balcony", "area": 110, "x": 0.5, "y": 0.5, "width": 14.0, "height": 7.8, "vastu_zone": "E"}
            ]
        },
        {
            "id": "sample-3bhk-atrium",
            "code": "3 BHK Central Atrium",
            "title": "Vastu Biophilic Courtyard Residence",
            "area": 2400,
            "bedrooms": 3,
            "bathrooms": 3,
            "layoutShape": "courtyard",
            "plot_w": 42.0,
            "plot_h": 55.0,
            "rooms": [
                {"name": "Grand Drawing Room", "type": "living", "area": 380, "x": 1.0, "y": 1.0, "width": 18.0, "height": 21.1, "vastu_zone": "NE"},
                {"name": "Dining Pavilion", "type": "dining", "area": 210, "x": 20.0, "y": 1.0, "width": 14.0, "height": 15.0, "vastu_zone": "E"},
                {"name": "Modular Island Kitchen", "type": "kitchen", "area": 190, "x": 20.0, "y": 16.5, "width": 14.0, "height": 13.5, "vastu_zone": "SE"},
                {"name": "Pooja Sanctum", "type": "pooja", "area": 60, "x": 34.5, "y": 1.0, "width": 6.5, "height": 9.2, "vastu_zone": "NE"},
                {"name": "Master Suite", "type": "bedroom", "area": 360, "x": 1.0, "y": 32.0, "width": 18.0, "height": 20.0, "vastu_zone": "SW"},
                {"name": "Master Ensuite Bath", "type": "bathroom", "area": 95, "x": 1.0, "y": 23.0, "width": 11.0, "height": 8.6, "vastu_zone": "SW"},
                {"name": "Bedroom 2 (Garden Facing)", "type": "bedroom", "area": 220, "x": 20.0, "y": 31.0, "width": 14.0, "height": 15.7, "vastu_zone": "NW"},
                {"name": "Bedroom 3 (Study Attached)", "type": "bedroom", "area": 200, "x": 20.0, "y": 47.0, "width": 14.0, "height": 14.2, "vastu_zone": "N"},
                {"name": "Common Bathroom", "type": "bathroom", "area": 65, "x": 34.5, "y": 31.0, "width": 6.5, "height": 10.0, "vastu_zone": "W"},
                {"name": "Verandah Terrace", "type": "balcony", "area": 140, "x": 1.0, "y": 52.5, "width": 18.0, "height": 7.7, "vastu_zone": "S"}
            ]
        }
    ]
    return {
        "success": True,
        "data": samples
    }
