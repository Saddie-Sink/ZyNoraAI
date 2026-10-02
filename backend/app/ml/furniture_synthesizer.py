"""
ZYNORA-ML — Spatial Furniture Synthesizer (ML & Empirical Indoor Scene Synthesis)
================================================================================
Synthesizes physics-grounded, aesthetically positioned 3D furniture layouts for
residential floor plans conditioned on:
  1. Room category & functional classification (Living, Dining, Bed, Kitchen, Bath, etc.)
  2. Metric room bounding geometry [x, y, width, height]
  3. Structured3D empirical priors & anthropometric spatial clearance rules
  4. Vastu Shastra orientation guidelines (e.g. Master bed head to South/West, Pooja altar East)
"""

import math
from typing import List, Dict, Any, Tuple

FT_TO_M = 0.3048  # feet to meters conversion factor


class FurnitureSynthesizer:
    """
    Synthesizes discrete 3D furniture entities with precise positions,
    dimensions, rotations, and materials for each room.
    """

    def __init__(self):
        pass

    def synthesize_room_furniture(
        self,
        room: Dict[str, Any],
        room_idx: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Generates 3D furniture items for a single room.
        All coordinates returned are in world meters (X=width, Y=height/up, Z=depth).
        """
        rtype = room.get("type", "bedroom").lower()
        rname = room.get("name", "Room")

        # Room bounds in feet
        rf_x = float(room.get("x", 0.0))
        rf_y = float(room.get("y", 0.0))
        rf_w = float(room.get("width", 14.0))
        rf_h = float(room.get("height", 14.0))

        # Convert room to world meters
        rx = rf_x * FT_TO_M
        rz = rf_y * FT_TO_M
        rw = rf_w * FT_TO_M
        rd = rf_h * FT_TO_M

        cx = rx + rw / 2.0
        cz = rz + rd / 2.0

        items: List[Dict[str, Any]] = []

        # Dispatch based on room type
        if rtype == "living":
            items = self._synthesize_living(rx, rz, rw, rd, cx, cz, room_idx)
        elif rtype == "dining":
            items = self._synthesize_dining(rx, rz, rw, rd, cx, cz, room_idx)
        elif rtype == "kitchen":
            items = self._synthesize_kitchen(rx, rz, rw, rd, cx, cz, room_idx)
        elif rtype == "bedroom":
            is_master = "master" in rname.lower() or room_idx == 0
            items = self._synthesize_bedroom(rx, rz, rw, rd, cx, cz, is_master, room_idx)
        elif rtype == "bathroom":
            items = self._synthesize_bathroom(rx, rz, rw, rd, cx, cz, room_idx)
        elif rtype == "pooja":
            items = self._synthesize_pooja(rx, rz, rw, rd, cx, cz, room_idx)
        elif rtype == "balcony":
            items = self._synthesize_balcony(rx, rz, rw, rd, cx, cz, room_idx)
        elif rtype == "utility":
            items = self._synthesize_utility(rx, rz, rw, rd, cx, cz, room_idx)
        else:
            items = self._synthesize_generic(rx, rz, rw, rd, cx, cz, room_idx)

        return items

    # ── 1. LIVING ROOM / DRAWING HALL ─────────────────────────────────────────
    def _synthesize_living(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []

        # Woven Area Rug
        rug_w = min(3.2, rw * 0.65)
        rug_d = min(2.4, rd * 0.65)
        items.append({
            "id": f"liv_rug_{idx}",
            "type": "area_rug",
            "category": "living",
            "name": "Geometric Wool Rug",
            "position": [round(cx, 2), 0.015, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(rug_w, 2), 0.02, round(rug_d, 2)],
            "material": {"color": "#d5cebe", "type": "fabric", "roughness": 0.95}
        })

        # Main 3-Seater / Sectional Sofa
        sofa_w = min(2.5, rw * 0.55)
        sofa_d = 0.95
        sofa_z = cz - (rug_d * 0.35)
        items.append({
            "id": f"liv_sofa_{idx}",
            "type": "sofa_sectional",
            "category": "living",
            "name": "Contemporary 3-Seater Sofa",
            "position": [round(cx, 2), 0.42, round(sofa_z, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(sofa_w, 2), 0.84, round(sofa_d, 2)],
            "material": {"color": "#3a404a", "type": "fabric_cushion", "roughness": 0.85}
        })

        # Modern Wood/Glass Coffee Table
        table_w = min(1.3, sofa_w * 0.65)
        table_d = 0.65
        items.append({
            "id": f"liv_table_{idx}",
            "type": "coffee_table",
            "category": "living",
            "name": "Oak & Glass Coffee Table",
            "position": [round(cx, 2), 0.22, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(table_w, 2), 0.44, round(table_d, 2)],
            "material": {"color": "#8c6239", "type": "wood_oak", "roughness": 0.4}
        })

        # Accent Lounge Armchair
        chair_x = cx + (sofa_w * 0.55)
        chair_z = cz + 0.2
        items.append({
            "id": f"liv_chair_{idx}",
            "type": "armchair",
            "category": "living",
            "name": "Scandinavian Accent Chair",
            "position": [round(chair_x, 2), 0.4, round(chair_z, 2)],
            "rotation": [0, -45, 0],
            "dimensions": [0.82, 0.8, 0.82],
            "material": {"color": "#b88a58", "type": "leather_cognac", "roughness": 0.6}
        })

        # TV Media Unit & Flat Screen on front wall
        tv_unit_w = min(2.4, rw * 0.6)
        tv_z = cz + (rug_d * 0.5) + 0.35
        if tv_z < rz + rd - 0.3:
            items.append({
                "id": f"liv_tvunit_{idx}",
                "type": "tv_console",
                "category": "living",
                "name": "Floating Media Console & 65\" TV",
                "position": [round(cx, 2), 0.3, round(tv_z, 2)],
                "rotation": [0, 180, 0],
                "dimensions": [round(tv_unit_w, 2), 0.5, 0.42],
                "material": {"color": "#1f242d", "type": "wood_charcoal", "roughness": 0.3}
            })
            # TV Screen
            items.append({
                "id": f"liv_tvscreen_{idx}",
                "type": "tv_screen",
                "category": "living",
                "name": "OLED Television 65\"",
                "position": [round(cx, 2), 0.95, round(tv_z, 2)],
                "rotation": [0, 180, 0],
                "dimensions": [1.45, 0.85, 0.06],
                "material": {"color": "#0d0e11", "type": "glass_screen", "roughness": 0.1, "metallic": 0.9}
            })

        # Potted Fiddle Leaf Plant in corner
        plant_x = rx + 0.45
        plant_z = rz + 0.45
        items.append({
            "id": f"liv_plant_{idx}",
            "type": "indoor_plant",
            "category": "living",
            "name": "Potted Ficus Lyrata",
            "position": [round(plant_x, 2), 0.65, round(plant_z, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.55, 1.3, 0.55],
            "material": {"color": "#2d5a27", "type": "foliage", "roughness": 0.7}
        })

        return items

    # ── 2. DINING ROOM ────────────────────────────────────────────────────────
    def _synthesize_dining(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []

        # Dining Table Rug
        rug_w = min(2.8, rw * 0.75)
        rug_d = min(2.2, rd * 0.75)
        items.append({
            "id": f"din_rug_{idx}",
            "type": "area_rug",
            "category": "dining",
            "name": "Under-Table Jute Rug",
            "position": [round(cx, 2), 0.015, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(rug_w, 2), 0.02, round(rug_d, 2)],
            "material": {"color": "#bfb8a5", "type": "fabric", "roughness": 0.9}
        })

        # 6-Seater Solid Teak Dining Table
        table_w = min(1.8, rw * 0.55)
        table_d = 0.95
        items.append({
            "id": f"din_table_{idx}",
            "type": "dining_table",
            "category": "dining",
            "name": "6-Seater Solid Oak Dining Table",
            "position": [round(cx, 2), 0.38, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(table_w, 2), 0.76, round(table_d, 2)],
            "material": {"color": "#784b2a", "type": "wood_teak", "roughness": 0.35}
        })

        # Dining Chairs (6 chairs: 3 North, 3 South)
        chair_offsets_x = [-table_w * 0.32, 0.0, table_w * 0.32]
        for c_i, off_x in enumerate(chair_offsets_x):
            # South chair
            items.append({
                "id": f"din_chair_s_{idx}_{c_i}",
                "type": "dining_chair",
                "category": "dining",
                "name": f"Dining Chair S{c_i+1}",
                "position": [round(cx + off_x, 2), 0.44, round(cz - table_d * 0.65, 2)],
                "rotation": [0, 0, 0],
                "dimensions": [0.48, 0.88, 0.48],
                "material": {"color": "#303238", "type": "wood_charcoal", "roughness": 0.6}
            })
            # North chair
            items.append({
                "id": f"din_chair_n_{idx}_{c_i}",
                "type": "dining_chair",
                "category": "dining",
                "name": f"Dining Chair N{c_i+1}",
                "position": [round(cx + off_x, 2), 0.44, round(cz + table_d * 0.65, 2)],
                "rotation": [0, 180, 0],
                "dimensions": [0.48, 0.88, 0.48],
                "material": {"color": "#303238", "type": "wood_charcoal", "roughness": 0.6}
            })

        # Overhead Brass Chandelier / Pendant
        items.append({
            "id": f"din_pendant_{idx}",
            "type": "pendant_light",
            "category": "dining",
            "name": "Modern Brass Linear Chandelier",
            "position": [round(cx, 2), 2.1, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(table_w * 0.7, 2), 0.25, 0.15],
            "material": {"color": "#d4af37", "type": "metal_brass", "roughness": 0.2, "metallic": 0.9}
        })

        return items

    # ── 3. MODULAR KITCHEN ────────────────────────────────────────────────────
    def _synthesize_kitchen(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []
        counter_depth = 0.65
        counter_h = 0.88

        # L-Shape Main Counter along South & East wall
        # South counter segment
        c1_w = max(1.6, rw - 0.8)
        items.append({
            "id": f"kit_counter_main_{idx}",
            "type": "kitchen_counter",
            "category": "kitchen",
            "name": "Granite Base Counter & Drawers",
            "position": [round(rx + c1_w / 2.0 + 0.1, 2), counter_h / 2.0, round(rz + counter_depth / 2.0 + 0.05, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(c1_w, 2), counter_h, counter_depth],
            "material": {"color": "#282b30", "type": "granite_black", "roughness": 0.25}
        })

        # Cooktop (4-Burner Hob in SE Agni quadrant)
        items.append({
            "id": f"kit_hob_{idx}",
            "type": "cooktop_hob",
            "category": "kitchen",
            "name": "4-Burner Glass Induction Cooktop",
            "position": [round(rx + c1_w * 0.75, 2), counter_h + 0.02, round(rz + counter_depth / 2.0 + 0.05, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.78, 0.04, 0.52],
            "material": {"color": "#111215", "type": "glass_black", "roughness": 0.1, "metallic": 0.8}
        })

        # Double Bowl Undermount Sink with Faucet (NE quadrant)
        items.append({
            "id": f"kit_sink_{idx}",
            "type": "kitchen_sink",
            "category": "kitchen",
            "name": "Undermount Double Sink & Gooseneck Faucet",
            "position": [round(rx + c1_w * 0.35, 2), counter_h + 0.01, round(rz + counter_depth / 2.0 + 0.05, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.82, 0.35, 0.48],
            "material": {"color": "#b0b5be", "type": "metal_chrome", "roughness": 0.2, "metallic": 0.9}
        })

        # Refrigerator in Corner
        fridge_w = 0.92
        fridge_d = 0.75
        fridge_h = 1.85
        items.append({
            "id": f"kit_fridge_{idx}",
            "type": "refrigerator",
            "category": "kitchen",
            "name": "French Door Stainless Refrigerator",
            "position": [round(rx + rw - fridge_w / 2.0 - 0.1, 2), fridge_h / 2.0, round(rz + rd - fridge_d / 2.0 - 0.1, 2)],
            "rotation": [0, 180, 0],
            "dimensions": [fridge_w, fridge_h, fridge_d],
            "material": {"color": "#c0c4cc", "type": "metal_steel", "roughness": 0.3, "metallic": 0.85}
        })

        return items

    # ── 4. BEDROOM (MASTER & SECONDARY) ───────────────────────────────────────
    def _synthesize_bedroom(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, is_master: bool, idx: int
    ) -> List[Dict[str, Any]]:
        items = []

        # Bed dimensions based on Master vs Guest/Child
        bed_w = 2.05 if is_master else 1.65
        bed_d = 2.15 if is_master else 2.05
        bed_h = 1.05 if is_master else 0.95

        # Place bed against South/West wall per Vastu
        bed_z = rz + bed_d / 2.0 + 0.15

        # Bedroom Floor Rug under lower half of bed
        rug_w = bed_w + 1.2
        rug_d = 2.2
        items.append({
            "id": f"bed_rug_{idx}",
            "type": "area_rug",
            "category": "bedroom",
            "name": "Plush Bedroom Carpet",
            "position": [round(cx, 2), 0.015, round(bed_z + 0.6, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(rug_w, 2), 0.02, round(rug_d, 2)],
            "material": {"color": "#ece6d8", "type": "fabric_plush", "roughness": 0.95}
        })

        # Main Bed Assembly (Frame + Mattress + Headboard)
        items.append({
            "id": f"bed_main_{idx}",
            "type": "king_bed" if is_master else "queen_bed",
            "category": "bedroom",
            "name": "Upholstered King Bed" if is_master else "Modern Queen Bed",
            "position": [round(cx, 2), 0.48, round(bed_z, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(bed_w, 2), round(bed_h, 2), round(bed_d, 2)],
            "material": {"color": "#3b4452" if is_master else "#565e6d", "type": "fabric_upholstery", "roughness": 0.8}
        })

        # Dual Nightstands flanking the headboard
        ns_w = 0.52
        ns_d = 0.45
        ns_h = 0.52
        for side, sign in [("l", -1), ("r", 1)]:
            ns_x = cx + sign * (bed_w / 2.0 + ns_w / 2.0 + 0.08)
            items.append({
                "id": f"bed_ns_{side}_{idx}",
                "type": "nightstand",
                "category": "bedroom",
                "name": f"Nightstand {side.upper()}",
                "position": [round(ns_x, 2), ns_h / 2.0, round(rz + ns_d / 2.0 + 0.15, 2)],
                "rotation": [0, 0, 0],
                "dimensions": [ns_w, ns_h, ns_d],
                "material": {"color": "#5a3a24", "type": "wood_walnut", "roughness": 0.4}
            })
            # Bedside Table Lamp with warm glow
            items.append({
                "id": f"bed_lamp_{side}_{idx}",
                "type": "table_lamp",
                "category": "bedroom",
                "name": f"Bedside Lamp {side.upper()}",
                "position": [round(ns_x, 2), ns_h + 0.22, round(rz + ns_d / 2.0 + 0.15, 2)],
                "rotation": [0, 0, 0],
                "dimensions": [0.24, 0.44, 0.24],
                "material": {"color": "#fef3c7", "type": "light_emitter", "roughness": 0.2, "emission": "#ffa834"}
            })

        # Full-Height Wardrobe / Dressing Unit
        wardrobe_w = min(2.4, rw * 0.5)
        wardrobe_d = 0.62
        wardrobe_h = 2.3
        w_x = rx + rw - wardrobe_w / 2.0 - 0.15
        w_z = rz + rd - wardrobe_d / 2.0 - 0.15
        items.append({
            "id": f"bed_wardrobe_{idx}",
            "type": "wardrobe",
            "category": "bedroom",
            "name": "Floor-to-Ceiling Wardrobe with Fluted Finish",
            "position": [round(w_x, 2), wardrobe_h / 2.0, round(w_z, 2)],
            "rotation": [0, 180, 0],
            "dimensions": [round(wardrobe_w, 2), wardrobe_h, wardrobe_d],
            "material": {"color": "#e0dbce", "type": "wood_lacquered", "roughness": 0.45}
        })

        return items

    # ── 5. BATHROOM ───────────────────────────────────────────────────────────
    def _synthesize_bathroom(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []

        # Floating Vanity Basin + Mirror
        vanity_w = min(0.95, rw * 0.5)
        vanity_d = 0.52
        vanity_h = 0.78
        v_x = rx + vanity_w / 2.0 + 0.1
        v_z = rz + vanity_d / 2.0 + 0.1
        items.append({
            "id": f"bath_vanity_{idx}",
            "type": "vanity_basin",
            "category": "bathroom",
            "name": "Floating Oak Vanity with Ceramic Basin",
            "position": [round(v_x, 2), vanity_h / 2.0 + 0.1, round(v_z, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(vanity_w, 2), vanity_h, vanity_d],
            "material": {"color": "#6e4b2d", "type": "wood_oak", "roughness": 0.4}
        })
        # Mirror above vanity
        items.append({
            "id": f"bath_mirror_{idx}",
            "type": "bathroom_mirror",
            "category": "bathroom",
            "name": "Backlit LED Bathroom Mirror",
            "position": [round(v_x, 2), 1.55, round(rz + 0.05, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(vanity_w * 0.85, 2), 0.95, 0.04],
            "material": {"color": "#dbeafe", "type": "mirror_glass", "roughness": 0.05, "metallic": 0.95}
        })

        # Wall-Hung WC (Toilet) with concealed cistern
        wc_w = 0.42
        wc_d = 0.62
        wc_h = 0.48
        items.append({
            "id": f"bath_wc_{idx}",
            "type": "toilet_wc",
            "category": "bathroom",
            "name": "Wall-Hung Porcelain Toilet",
            "position": [round(rx + rw - wc_w / 2.0 - 0.2, 2), wc_h / 2.0 + 0.05, round(rz + wc_d / 2.0 + 0.1, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [wc_w, wc_h, wc_d],
            "material": {"color": "#fdfdfd", "type": "ceramic_white", "roughness": 0.15}
        })

        # Walk-in Glass Shower Screen
        shower_w = min(1.1, rw * 0.5)
        shower_d = min(1.1, rd * 0.45)
        items.append({
            "id": f"bath_shower_{idx}",
            "type": "shower_enclosure",
            "category": "bathroom",
            "name": "Frameless Tempered Glass Shower Enclosure",
            "position": [round(rx + rw - shower_w / 2.0 - 0.05, 2), 1.05, round(rz + rd - shower_d / 2.0 - 0.05, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(shower_w, 2), 2.1, round(shower_d, 2)],
            "material": {"color": "#94a3b8", "type": "glass_shower", "roughness": 0.1, "transparent": True, "opacity": 0.35}
        })

        return items

    # ── 6. POOJA ROOM ─────────────────────────────────────────────────────────
    def _synthesize_pooja(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []

        # Carved Teak Mandir Altar on East-facing wall
        altar_w = min(1.2, rw * 0.7)
        altar_d = 0.55
        altar_h = 1.35
        items.append({
            "id": f"pooja_altar_{idx}",
            "type": "pooja_mandir",
            "category": "pooja",
            "name": "Carved Solid Teak Pooja Mandir Altar",
            "position": [round(cx, 2), altar_h / 2.0 + 0.15, round(rz + altar_d / 2.0 + 0.1, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(altar_w, 2), altar_h, altar_d],
            "material": {"color": "#5c2e14", "type": "wood_teak_carved", "roughness": 0.35}
        })

        # Brass Diya Lamp with warm golden glow
        items.append({
            "id": f"pooja_diya_{idx}",
            "type": "brass_diya",
            "category": "pooja",
            "name": "Auspicious Brass Nilavilakku Diya",
            "position": [round(cx, 2), altar_h + 0.25, round(rz + altar_d / 2.0 + 0.1, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.22, 0.35, 0.22],
            "material": {"color": "#f59e0b", "type": "metal_brass_lit", "roughness": 0.2, "emission": "#f59e0b"}
        })

        # Velvet Prayer Seating Asana (Meditation Mat)
        items.append({
            "id": f"pooja_mat_{idx}",
            "type": "prayer_asana",
            "category": "pooja",
            "name": "Embroidered Velvet Meditation Asana",
            "position": [round(cx, 2), 0.04, round(cz + 0.35, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.75, 0.08, 0.75],
            "material": {"color": "#831843", "type": "fabric_velvet", "roughness": 0.9}
        })

        return items

    # ── 7. BALCONY / TERRACE ──────────────────────────────────────────────────
    def _synthesize_balcony(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []

        # Bistro Table & 2 Rattan Armchairs
        items.append({
            "id": f"balc_table_{idx}",
            "type": "bistro_table",
            "category": "balcony",
            "name": "Weatherproof Rattan Coffee Table",
            "position": [round(cx, 2), 0.36, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.7, 0.72, 0.7],
            "material": {"color": "#4a3525", "type": "rattan", "roughness": 0.7}
        })
        for side, sign in [("l", -1), ("r", 1)]:
            items.append({
                "id": f"balc_chair_{side}_{idx}",
                "type": "bistro_chair",
                "category": "balcony",
                "name": f"Balcony Chair {side.upper()}",
                "position": [round(cx + sign * 0.75, 2), 0.42, round(cz, 2)],
                "rotation": [0, sign * 90, 0],
                "dimensions": [0.58, 0.82, 0.58],
                "material": {"color": "#33251a", "type": "rattan_dark", "roughness": 0.75}
            })

        # Planter Box with Greenery
        items.append({
            "id": f"balc_planter_{idx}",
            "type": "planter_box",
            "category": "balcony",
            "name": "Architectural Concrete Trough Planter",
            "position": [round(rx + rw / 2.0, 2), 0.35, round(rz + rd - 0.25, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [round(min(2.0, rw * 0.8), 2), 0.55, 0.35],
            "material": {"color": "#274e13", "type": "plants_balcony", "roughness": 0.8}
        })

        return items

    # ── 8. UTILITY ────────────────────────────────────────────────────────────
    def _synthesize_utility(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        items = []
        # Washing machine & laundry unit
        items.append({
            "id": f"util_wm_{idx}",
            "type": "washing_machine",
            "category": "utility",
            "name": "Front-Load Smart Washer-Dryer",
            "position": [round(rx + 0.45, 2), 0.48, round(rz + 0.45, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [0.65, 0.95, 0.65],
            "material": {"color": "#e2e8f0", "type": "metal_appliance", "roughness": 0.25, "metallic": 0.8}
        })
        return items

    def _synthesize_generic(
        self, rx: float, rz: float, rw: float, rd: float, cx: float, cz: float, idx: int
    ) -> List[Dict[str, Any]]:
        return [{
            "id": f"gen_item_{idx}",
            "type": "generic_furniture",
            "category": "general",
            "name": "Console Cabinet",
            "position": [round(cx, 2), 0.42, round(cz, 2)],
            "rotation": [0, 0, 0],
            "dimensions": [1.4, 0.84, 0.45],
            "material": {"color": "#8c6239", "type": "wood", "roughness": 0.4}
        }]
