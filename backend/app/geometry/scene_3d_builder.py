"""
ZYNORA-ML — 3D Scene Graph Builder (Floorplan to 3D Synthesis Engine)
====================================================================
Transforms 2D metric floor plans into rich, physical 3D Dollhouse scene graphs
incorporating:
  1. Structured3D Neural Extrusion (predicts wall heights, slab thickness, openings)
  2. Spatial Furniture Synthesizer (places 3D furniture with clearance & orientation)
  3. PBR Material mapping (hardwood herringbone, Calacatta marble, slate tile)
  4. Precise 3D wall segments with door/window aperture cutouts
  5. Multi-angle architectural camera presets (Isometric Dollhouse, Top-Down, Eye-Level)
"""

from typing import List, Dict, Any, Tuple
from backend.app.ml.furniture_synthesizer import FurnitureSynthesizer, FT_TO_M
from backend.app.ml.model_registry import ModelRegistry


# ─── PBR Material Specifications ──────────────────────────────────────────────
FLOOR_MATERIALS = {
    "living": {
        "key": "herringbone_oak",
        "name": "Natural European White Oak Herringbone Parquet",
        "color": "#c8a57a",
        "roughness": 0.45,
        "metalness": 0.05,
        "tileScale": [1.2, 1.2],
    },
    "dining": {
        "key": "herringbone_oak",
        "name": "Natural European White Oak Herringbone Parquet",
        "color": "#c29e73",
        "roughness": 0.45,
        "metalness": 0.05,
        "tileScale": [1.2, 1.2],
    },
    "kitchen": {
        "key": "calacatta_marble",
        "name": "Polished Calacatta Gold Statuario Marble",
        "color": "#eceae4",
        "roughness": 0.18,
        "metalness": 0.1,
        "tileScale": [2.0, 2.0],
    },
    "bedroom": {
        "key": "plank_teak",
        "name": "Nilambur Teak Wide Planks",
        "color": "#9e6f47",
        "roughness": 0.42,
        "metalness": 0.05,
        "tileScale": [1.5, 1.5],
    },
    "bathroom": {
        "key": "slate_tile",
        "name": "Honed Anthracite Slate Tile",
        "color": "#2c3038",
        "roughness": 0.6,
        "metalness": 0.15,
        "tileScale": [0.8, 0.8],
    },
    "pooja": {
        "key": "makrana_marble",
        "name": "Auspicious Pure White Makrana Marble",
        "color": "#f8f7f2",
        "roughness": 0.22,
        "metalness": 0.08,
        "tileScale": [1.8, 1.8],
    },
    "balcony": {
        "key": "stone_pavers",
        "name": "Flamed Granite Weatherproof Pavers",
        "color": "#787672",
        "roughness": 0.75,
        "metalness": 0.05,
        "tileScale": [1.0, 1.0],
    },
    "utility": {
        "key": "ceramic_grey",
        "name": "Anti-Skid Matte Ceramic Tile",
        "color": "#8c929d",
        "roughness": 0.65,
        "metalness": 0.05,
        "tileScale": [0.6, 0.6],
    },
}


class Scene3DBuilder:
    """
    Assembles complete 3D Dollhouse architectural scenes from 2D room layouts.
    """

    def __init__(self):
        self.furniture_synth = FurnitureSynthesizer()

    def build_scene(
        self,
        floorplan: Dict[str, Any],
        cutaway_height: float = 1.8  # meters for dollhouse slice
    ) -> Dict[str, Any]:
        """
        Main 3D Scene synthesis entry point.
        """
        rooms_input = floorplan.get("rooms", [])
        cand_id = floorplan.get("id", "cand-a")
        cand_code = floorplan.get("code", "Candidate A")
        cand_title = floorplan.get("title", "Floorplan to 3D")
        plot_info = floorplan.get("plotInfo", {})

        # Predict neural extrusions using Structured3D model if available
        registry = ModelRegistry.get_instance()
        rooms_with_ext = registry.predict_room_extrusions(rooms_input, floor_idx=0)

        # Plot dimensions in meters
        plot_w_ft = float(plot_info.get("plot_w", 40.0) or 40.0)
        plot_h_ft = float(plot_info.get("plot_h", 60.0) or 60.0)
        total_w_m = round(plot_w_ft * FT_TO_M, 2)
        total_d_m = round(plot_h_ft * FT_TO_M, 2)

        # Average wall height from ML model
        avg_wall_h_ft = sum(r.get("wall_height_ft", 10.0) for r in rooms_with_ext) / max(1, len(rooms_with_ext))
        wall_h_m = round(avg_wall_h_ft * FT_TO_M, 2)

        scene_rooms = []
        all_furniture = []
        wall_segments = []

        # Process each room
        for idx, room in enumerate(rooms_with_ext):
            rf_x = float(room.get("x", 0.0) or 0.0)
            rf_y = float(room.get("y", 0.0) or 0.0)
            rf_w = float(room.get("width", 14.0) or 14.0)
            rf_h = float(room.get("height", 14.0) or 14.0)

            rx = round(rf_x * FT_TO_M, 3)
            rz = round(rf_y * FT_TO_M, 3)
            rw = round(rf_w * FT_TO_M, 3)
            rd = round(rf_h * FT_TO_M, 3)

            cx = round(rx + rw / 2.0, 3)
            cz = round(rz + rd / 2.0, 3)

            rtype = room.get("type", "bedroom").lower()
            rname = room.get("name", f"Room {idx+1}")
            vastu_z = room.get("vastu_zone", "C")
            area_sqft = int(room.get("area", round(rf_w * rf_h)))

            # Floor material
            mat_spec = FLOOR_MATERIALS.get(rtype, FLOOR_MATERIALS["bedroom"])

            # Synthesize 3D furniture
            furn_items = self.furniture_synth.synthesize_room_furniture(room, room_idx=idx)
            all_furniture.extend(furn_items)

            # Room wall segments (4 walls around room bounding box)
            # Wall thickness: 0.12m interior, 0.23m exterior boundary
            is_ext_s = (rf_y <= 1.0)
            is_ext_n = (rf_y + rf_h >= plot_h_ft - 1.0)
            is_ext_w = (rf_x <= 1.0)
            is_ext_e = (rf_x + rf_w >= plot_w_ft - 1.0)

            r_walls = [
                # South wall: (rx, rz) to (rx + rw, rz)
                {"p1": [rx, rz], "p2": [rx + rw, rz], "isExterior": is_ext_s, "orientation": "S"},
                # East wall: (rx + rw, rz) to (rx + rw, rz + rd)
                {"p1": [rx + rw, rz], "p2": [rx + rw, rz + rd], "isExterior": is_ext_e, "orientation": "E"},
                # North wall: (rx + rw, rz + rd) to (rx, rz + rd)
                {"p1": [rx + rw, rz + rd], "p2": [rx, rz + rd], "isExterior": is_ext_n, "orientation": "N"},
                # West wall: (rx, rz + rd) to (rx, rz)
                {"p1": [rx, rz + rd], "p2": [rx, rz], "isExterior": is_ext_w, "orientation": "W"},
            ]
            wall_segments.extend(r_walls)

            # Door position (connecting to circulation or entrance)
            door_pos = [cx, rz] if not is_ext_s else [rx, cz]

            # Window position (on exterior wall if available)
            win_pos = None
            if is_ext_n:
                win_pos = [cx, rz + rd, 1.8, 1.2]
            elif is_ext_s:
                win_pos = [cx, rz, 1.8, 1.2]
            elif is_ext_e:
                win_pos = [rx + rw, cz, 1.8, 1.2]
            elif is_ext_w:
                win_pos = [rx, cz, 1.8, 1.2]

            scene_rooms.append({
                "id": f"room_{idx}",
                "name": rname,
                "type": rtype,
                "vastuZone": vastu_z,
                "areaSqFt": area_sqft,
                "bounds": [rx, rz, rw, rd],
                "center": [cx, cz],
                "wallHeightMeters": wall_h_m,
                "flooring": mat_spec,
                "door": {
                    "position": door_pos,
                    "width": 0.95,
                    "height": 2.1
                },
                "window": {
                    "position": win_pos[:2] if win_pos else None,
                    "width": win_pos[2] if win_pos else 0,
                    "height": win_pos[3] if win_pos else 0,
                    "sillHeight": 0.85
                } if win_pos else None,
                "furnitureCount": len(furn_items),
                "cameraTarget": [cx, 1.55, cz],
            })

        # Calculate bounding box of the whole house
        center_x = total_w_m / 2.0
        center_z = total_d_m / 2.0

        # Architectural Camera Presets
        camera_presets = {
            "isometric_45": {
                "name": "45° Isometric Dollhouse",
                "subTitle": "Three-quarter oblique cutaway viewing entire layout and furniture",
                "position": [round(center_x + total_w_m * 0.95, 2), round(wall_h_m * 4.2, 2), round(center_z + total_d_m * 1.05, 2)],
                "target": [round(center_x, 2), 0.5, round(center_z, 2)],
                "fov": 38,
            },
            "top_down_3d": {
                "name": "Top-Down 3D Orthographic",
                "subTitle": "Direct overhead architectural perspective with realistic 3D materials",
                "position": [round(center_x, 2), round(max(total_w_m, total_d_m) * 1.8, 2), round(center_z + 0.01, 2)],
                "target": [round(center_x, 2), 0.0, round(center_z, 2)],
                "fov": 32,
            },
            "front_perspective": {
                "name": "Front Angle Entryway",
                "subTitle": "Low-angle arrival perspective focusing on entrance and drawing room",
                "position": [round(center_x, 2), 2.2, round(-total_d_m * 0.35, 2)],
                "target": [round(center_x, 2), 1.2, round(center_z * 0.5, 2)],
                "fov": 50,
            }
        }

        # Lighting Configuration
        lighting = {
            "sun": {
                "position": [round(center_x + 18, 2), 32.0, round(center_z - 15, 2)],
                "color": "#fff6e5",
                "intensity": 2.2,
                "castShadow": True
            },
            "ambient": {
                "skyColor": "#93c5fd",
                "groundColor": "#3f3f46",
                "intensity": 0.75
            },
            "warmLED": {
                "color": "#ffa834",
                "intensity": 1.4,
                "coveHeight": round(cutaway_height - 0.05, 2)
            }
        }

        return {
            "candidateId": cand_id,
            "candidateCode": cand_code,
            "title": cand_title,
            "dimensions": {
                "widthMeters": total_w_m,
                "depthMeters": total_d_m,
                "heightMeters": wall_h_m,
                "widthFeet": plot_w_ft,
                "depthFeet": plot_h_ft,
                "wallHeightFeet": avg_wall_h_ft
            },
            "cutawayHeight": cutaway_height,
            "rooms": scene_rooms,
            "furniture": all_furniture,
            "walls": wall_segments,
            "lighting": lighting,
            "cameraPresets": camera_presets,
            "meta": {
                "totalRooms": len(scene_rooms),
                "totalFurnitureItems": len(all_furniture),
                "neuralExtrusionApplied": registry.extrusion_model is not None,
                "engine": "ZYNORA-ML Spatial 3D Synthesis Core v2.0"
            }
        }
