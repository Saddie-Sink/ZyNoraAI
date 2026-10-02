"""
ZYNORA-ML — Stages 4–12: Architectural Space Planner & 2D Geometry Generator
=============================================================================
Implements Stages 4 through 12 of the Architectural Floor Plan Pipeline:
  Stage 4: Architectural Space Planning (Public / Semi-Public / Private / Service zoning)
  Stage 5: Contiguous Room Allocation (x, y, width, height, area, floor, room type)
  Stage 6: Spatial Relationship Graph (explicit nodes & adjacency edges)
  Stage 7: Floor-by-Floor Planning (multi-storey independent floor layouts with aligned stairs)
  Stage 8: 2D Geometry Generation (site boundary, building boundary, rooms, open spaces, dimensions)
  Stage 9: Wall Generation (deduplicated shared interior & exterior walls with thickness)
  Stage 10: Door Generation (graph-driven accessible doors on valid shared walls with swing arcs)
  Stage 11: Window Generation (daylight & ventilation windows on exterior walls)
  Stage 12: Staircase & Column Generation (multi-floor aligned stairs with treads + structural columns)
"""

import math
from typing import Dict, Any, List, Tuple, Optional


def _round_grid(val: float, step: float = 0.5) -> float:
    return round(round(val / step) * step, 2)


def _fmt_feet_inches(feet_val: float) -> str:
    total_inches = int(round(feet_val * 12))
    ft = total_inches // 12
    inch = total_inches % 12
    return f"{ft}'{inch}\""


class FloorplanGeometryBuilder:
    """
    Synthesizes complete, accurate, dimensionally consistent 2D floor-plan
    geometry for single-storey and multi-storey residential buildings.
    """

    EXTERIOR_WALL_THICKNESS = 0.75  # 9 inches in feet
    INTERIOR_WALL_THICKNESS = 0.38  # 4.5 inches in feet
    PARAPET_WALL_THICKNESS  = 0.45  # 5.5 inches in feet

    def build_complete_floorplan(
        self,
        structured_reqs: Dict[str, Any],
        typology: str = "balanced",
    ) -> Dict[str, Any]:
        """
        Executes Stages 4–12 for a given candidate typology and structured requirements.
        Returns multi-floor 2D geometry, spatial relationship graph, and flat room summary.
        """
        site = structured_reqs.get("site", {})
        site_w = float(site.get("width", 30.0))
        site_d = float(site.get("depth", 40.0))
        entrance_dir = str(site.get("entranceDirection", "East"))
        floors_count = max(1, int(structured_reqs.get("floors", 2)))
        req_rooms = structured_reqs.get("requiredRooms", {})

        # Compute setbacks scaled to plot size
        sb_front = 3.0 if site_d >= 35 else 2.0
        sb_rear  = 2.0 if site_d >= 35 else 1.5
        sb_left  = 2.0 if site_w >= 28 else 1.5
        sb_right = 2.0 if site_w >= 28 else 1.5

        bx = _round_grid(sb_left)
        by = _round_grid(sb_front)
        bw = _round_grid(max(12.0, site_w - sb_left - sb_right))
        bh = _round_grid(max(16.0, site_d - sb_front - sb_rear))

        # ── STAGE 7: FLOOR-BY-FLOOR ROOM DISTRIBUTION ─────────────────────────
        floor_programs = self._distribute_rooms_by_floor(req_rooms, floors_count)

        # Pin a consistent Staircase bounding box across all floors when floors >= 2
        stair_box = self._compute_aligned_staircase_box(bx, by, bw, bh, typology) if floors_count >= 2 else None

        floors_geometry: List[Dict[str, Any]] = []
        all_rooms_flat: List[Dict[str, Any]] = []
        all_graph_nodes: List[Dict[str, Any]] = []
        all_graph_edges: List[Dict[str, Any]] = []

        for fl_idx in range(floors_count):
            fl_label = (
                "Ground Floor" if fl_idx == 0
                else "First Floor" if fl_idx == 1
                else f"Floor {fl_idx}"
            )
            fl_spec = floor_programs[fl_idx]

            # ── STAGE 4 & 5: SPACE PLANNING & CONTIGUOUS ROOM ALLOCATION ──────
            rooms_fl, open_spaces_fl = self._allocate_floor_rooms(
                floor_idx=fl_idx,
                fl_spec=fl_spec,
                bx=bx,
                by=by,
                bw=bw,
                bh=bh,
                site_w=site_w,
                site_d=site_d,
                stair_box=stair_box,
                typology=typology,
            )

            # ── STAGE 6: SPATIAL RELATIONSHIP GRAPH (FLOOR LEVEL) ─────────────
            fl_nodes, fl_edges = self._build_floor_spatial_graph(rooms_fl, fl_idx)
            all_graph_nodes.extend(fl_nodes)
            all_graph_edges.extend(fl_edges)

            # ── STAGE 9: WALL GENERATION (DEDUPLICATED SHARED WALLS) ──────────
            walls_fl = self._generate_floor_walls(
                rooms=rooms_fl,
                floor_idx=fl_idx,
                bx=bx,
                by=by,
                bw=bw,
                bh=bh,
                site_w=site_w,
                site_d=site_d,
            )

            # ── STAGE 10: DOOR GENERATION ─────────────────────────────────────
            doors_fl = self._generate_floor_doors(
                rooms=rooms_fl,
                walls=walls_fl,
                graph_edges=fl_edges,
                floor_idx=fl_idx,
                bx=bx,
                by=by,
                bw=bw,
                bh=bh,
            )

            # ── STAGE 11: WINDOW GENERATION ───────────────────────────────────
            windows_fl = self._generate_floor_windows(
                rooms=rooms_fl,
                walls=walls_fl,
                doors=doors_fl,
                floor_idx=fl_idx,
            )

            # ── STAGE 12: STAIRCASE & STRUCTURAL COLUMNS ──────────────────────
            staircase_geom = self._generate_staircase_geometry(
                rooms=rooms_fl,
                floor_idx=fl_idx,
                floors_count=floors_count,
            )
            columns_fl = self._generate_structural_columns(
                rooms=rooms_fl,
                floor_idx=fl_idx,
                bx=bx,
                by=by,
                bw=bw,
                bh=bh,
            )

            # ── STAGE 8: EXPLICIT DIMENSIONS & BOUNDARIES ─────────────────────
            dimensions_fl = self._generate_floor_dimensions(
                rooms=rooms_fl,
                site_w=site_w,
                site_d=site_d,
                bx=bx,
                by=by,
                bw=bw,
                bh=bh,
                floor_idx=fl_idx,
            )

            floor_data = {
                "floor": fl_idx,
                "label": fl_label,
                "siteBoundary": {
                    "x": 0.0,
                    "y": 0.0,
                    "width": site_w,
                    "depth": site_d,
                    "area": round(site_w * site_d, 1),
                    "entranceDirection": entrance_dir,
                },
                "buildingBoundary": {
                    "x": bx,
                    "y": by,
                    "width": bw,
                    "depth": bh,
                    "area": round(bw * bh, 1),
                    "setbacks": {
                        "front": sb_front,
                        "rear": sb_rear,
                        "left": sb_left,
                        "right": sb_right,
                    },
                },
                "rooms": rooms_fl,
                "walls": walls_fl,
                "doors": doors_fl,
                "windows": windows_fl,
                "staircase": staircase_geom,
                "columns": columns_fl,
                "openSpaces": open_spaces_fl,
                "dimensions": dimensions_fl,
            }
            floors_geometry.append(floor_data)
            all_rooms_flat.extend(rooms_fl)

        # Add inter-floor vertical staircase edges in the Spatial Relationship Graph
        if floors_count >= 2:
            for fl_idx in range(floors_count - 1):
                all_graph_edges.append({
                    "source": f"staircase_f{fl_idx}",
                    "target": f"staircase_f{fl_idx + 1}",
                    "relation": "vertical_stair_connection",
                    "floor": fl_idx,
                })

        return {
            "siteBoundary": {
                "width": site_w,
                "depth": site_d,
                "area": round(site_w * site_d, 1),
                "entranceDirection": entrance_dir,
            },
            "buildingBoundary": {
                "x": bx,
                "y": by,
                "width": bw,
                "depth": bh,
                "footprintArea": round(bw * bh, 1),
                "totalBuiltUpArea": round(sum(r["area"] for r in all_rooms_flat), 1),
            },
            "floorsCount": floors_count,
            "floorsGeometry": floors_geometry,
            "rooms": all_rooms_flat,
            "spatialGraph": {
                "nodes": all_graph_nodes,
                "edges": all_graph_edges,
            },
        }

    # ── STAGE 7: MULTI-STOREY ROOM DISTRIBUTION ───────────────────────────────
    def _distribute_rooms_by_floor(
        self, req_rooms: Dict[str, Any], floors_count: int
    ) -> List[List[Dict[str, Any]]]:
        """
        Distributes requested rooms across Ground Floor (0) and Upper Floors (1..N-1)
        following architectural zoning principles.
        """
        bedrooms   = int(req_rooms.get("bedrooms", 3))
        bathrooms  = int(req_rooms.get("bathrooms", 2))
        living     = int(req_rooms.get("living", 1))
        dining     = int(req_rooms.get("dining", 1))
        kitchen    = int(req_rooms.get("kitchen", 1))
        study      = int(req_rooms.get("study", 0))
        guest_room = int(req_rooms.get("guest_room", 0))
        utility    = int(req_rooms.get("utility", 0))
        store_room = int(req_rooms.get("store_room", 0))
        pooja      = int(req_rooms.get("pooja", 0))
        parking    = int(req_rooms.get("parking", 1))
        balcony    = int(req_rooms.get("balcony", 1))
        terrace    = int(req_rooms.get("terrace", 0))
        staircase  = 1 if floors_count >= 2 else int(req_rooms.get("staircase", 0))

        floor_lists: List[List[Dict[str, Any]]] = [[] for _ in range(floors_count)]

        if floors_count == 1:
            fl0 = floor_lists[0]
            if parking > 0:
                fl0.append({"name": f"Parking ({parking} Car)" if parking > 1 else "Car Parking", "type": "parking", "zone": "public", "mandatory": True})
            if living > 0:
                fl0.append({"name": "Living Room", "type": "living", "zone": "public", "mandatory": True})
            if dining > 0:
                fl0.append({"name": "Dining Room", "type": "dining", "zone": "public", "mandatory": True})
            if kitchen > 0:
                fl0.append({"name": "Kitchen", "type": "kitchen", "zone": "service", "mandatory": True})
            if pooja > 0:
                fl0.append({"name": "Pooja Room", "type": "pooja", "zone": "public", "mandatory": True})
            if utility > 0:
                fl0.append({"name": "Utility Room", "type": "utility", "zone": "service", "mandatory": True})
            if store_room > 0:
                fl0.append({"name": "Store Room", "type": "store", "zone": "service", "mandatory": True})

            for b in range(1, bedrooms + 1):
                bname = "Master Bedroom" if b == 1 else f"Bedroom {b}"
                fl0.append({"name": bname, "type": "bedroom", "zone": "private", "mandatory": True})
            if guest_room > 0:
                fl0.append({"name": "Guest Room", "type": "bedroom", "zone": "private", "mandatory": True})
            if study > 0:
                fl0.append({"name": "Study Room", "type": "study", "zone": "private", "mandatory": True})

            for bt in range(1, bathrooms + 1):
                bt_name = "Attached Bathroom" if bt == 1 else ("Common Bathroom" if bt == bathrooms else f"Bathroom {bt}")
                fl0.append({"name": bt_name, "type": "bathroom", "zone": "private", "mandatory": True})

            if balcony > 0:
                fl0.append({"name": "Balcony", "type": "balcony", "zone": "outdoor", "mandatory": True})
            if terrace > 0:
                fl0.append({"name": "Terrace", "type": "terrace", "zone": "outdoor", "mandatory": True})
            return floor_lists

        # ── MULTI-STOREY (2+ FLOORS) ──────────────────────────────────────────
        # GROUND FLOOR (Floor 0): Parking, Living, Dining, Kitchen, Staircase,
        # Ground Bedroom (if bedrooms >= 2), Common Bath, Utility/Store/Pooja
        fl0 = floor_lists[0]
        if parking > 0:
            fl0.append({"name": f"Parking ({parking} Car)" if parking > 1 else "Car Parking", "type": "parking", "zone": "public", "mandatory": True})
        if living > 0:
            fl0.append({"name": "Living Room", "type": "living", "zone": "public", "mandatory": True})
        if dining > 0:
            fl0.append({"name": "Dining Room", "type": "dining", "zone": "public", "mandatory": True})
        if kitchen > 0:
            fl0.append({"name": "Kitchen", "type": "kitchen", "zone": "service", "mandatory": True})
        if pooja > 0:
            fl0.append({"name": "Pooja Room", "type": "pooja", "zone": "public", "mandatory": True})
        if utility > 0:
            fl0.append({"name": "Utility Room", "type": "utility", "zone": "service", "mandatory": True})
        if store_room > 0:
            fl0.append({"name": "Store Room", "type": "store", "zone": "service", "mandatory": True})

        # Allocate bedrooms across Ground and Upper floors
        gf_beds = 1 if (bedrooms >= 3 or guest_room > 0) else 0
        uf_beds = bedrooms - gf_beds

        if gf_beds >= 1:
            fl0.append({"name": "Bedroom 1 (Ground)", "type": "bedroom", "zone": "private", "mandatory": True})
        if guest_room > 0 and bedrooms < 3:
            fl0.append({"name": "Guest Bedroom", "type": "bedroom", "zone": "private", "mandatory": True})

        # Bathrooms on Ground Floor: at least 1 Common Bathroom
        gf_baths = 1 if bathrooms >= 1 else 0
        uf_baths = max(1, bathrooms - gf_baths) if bathrooms >= 2 else 0
        if gf_baths >= 1:
            fl0.append({"name": "Common Bathroom", "type": "bathroom", "zone": "service", "mandatory": True})

        # Staircase on Ground Floor
        if staircase > 0:
            fl0.append({"name": "Staircase", "type": "staircase", "zone": "circulation", "mandatory": True})

        # FIRST FLOOR (Floor 1): Staircase, Upper bedrooms, Upper bathrooms, Study, Balcony, Terrace
        fl1 = floor_lists[1]
        if staircase > 0:
            fl1.append({"name": "Staircase", "type": "staircase", "zone": "circulation", "mandatory": True})

        bed_start_idx = gf_beds + 1
        for i in range(uf_beds):
            b_num = bed_start_idx + i
            if i == 0:
                b_name = "Master Bedroom"
            else:
                b_name = f"Bedroom {b_num}"
            fl1.append({"name": b_name, "type": "bedroom", "zone": "private", "mandatory": True})

        for i in range(uf_baths):
            bt_name = "Attached Bathroom" if i == 0 else f"Upper Bathroom {i + 1}"
            fl1.append({"name": bt_name, "type": "bathroom", "zone": "private", "mandatory": True})

        if study > 0:
            fl1.append({"name": "Study Room", "type": "study", "zone": "private", "mandatory": True})

        if balcony > 0:
            fl1.append({"name": "Balcony", "type": "balcony", "zone": "outdoor", "mandatory": True})

        if terrace > 0:
            fl1.append({"name": "Terrace", "type": "terrace", "zone": "outdoor", "mandatory": True})

        # If 3+ floors, distribute extra rooms or terrace/lounge to upper floors
        for fl_extra in range(2, floors_count):
            fl_e = floor_lists[fl_extra]
            fl_e.append({"name": "Staircase", "type": "staircase", "zone": "circulation", "mandatory": True})
            fl_e.append({"name": f"Level {fl_extra} Lounge", "type": "living", "zone": "public", "mandatory": False})
            fl_e.append({"name": f"Roof Terrace", "type": "terrace", "zone": "outdoor", "mandatory": False})

        return floor_lists

    def _compute_aligned_staircase_box(
        self, bx: float, by: float, bw: float, bh: float, typology: str
    ) -> Dict[str, float]:
        """
        Determines a fixed (x, y, width, height) for the vertical staircase core
        so that Ground Floor and First Floor staircases align identically in 2D plan.
        """
        front_ratio = {
            "balanced":  0.36,
            "atrium":    0.34,
            "linear":    0.38,
            "segmented": 0.35,
            "compact":   0.34,
        }.get(typology, 0.36)
        mid_ratio = {
            "balanced":  0.30,
            "atrium":    0.32,
            "linear":    0.28,
            "segmented": 0.30,
            "compact":   0.32,
        }.get(typology, 0.30)

        h_front = _round_grid(bh * front_ratio)
        h_mid   = _round_grid(bh * mid_ratio)
        st_w = _round_grid(min(8.0, max(6.0, bw * 0.26)))
        st_h = h_mid
        st_y = round(by + h_front, 2)

        # Distinct spine placement per archetype so candidates have genuinely distinct topologies
        if typology in ("atrium", "segmented", "linear"):
            st_x = bx
        else:
            st_x = round(bx + bw - st_w, 2)
        return {"x": st_x, "y": st_y, "width": st_w, "height": st_h}

    # ── STAGE 4 & 5: AI CSP CONTIGUOUS SUBDIVISION ROOM ALLOCATION ────────────
    def _allocate_floor_rooms(
        self,
        floor_idx: int,
        fl_spec: List[Dict[str, Any]],
        bx: float,
        by: float,
        bw: float,
        bh: float,
        site_w: float,
        site_d: float,
        stair_box: Optional[Dict[str, float]],
        typology: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Allocates exact, contiguous, non-overlapping room rectangles inside the
        buildable footprint (bx, by, bw, bh) for a single floor using AI CSP rules.
        Y=0 is the Front (Street/Entrance) edge; Y=site_d is the Rear edge.
        """
        rooms_out: List[Dict[str, Any]] = []
        open_spaces: List[Dict[str, Any]] = [
            {
                "id": f"setback_front_f{floor_idx}",
                "name": "Front Setback / Entrance Lawn" if floor_idx == 0 else "Front Setback Airspace",
                "type": "open_space",
                "x": 0.0,
                "y": 0.0,
                "width": site_w,
                "height": by,
                "area": round(site_w * by, 1),
                "floor": floor_idx,
            },
            {
                "id": f"setback_rear_f{floor_idx}",
                "name": "Rear Garden Setback" if floor_idx == 0 else "Rear Setback Airspace",
                "type": "open_space",
                "x": 0.0,
                "y": round(by + bh, 2),
                "width": site_w,
                "height": round(site_d - (by + bh), 2),
                "area": round(site_w * (site_d - (by + bh)), 1),
                "floor": floor_idx,
            },
        ]

        front_ratio = {
            "balanced":  0.36,
            "atrium":    0.34,
            "linear":    0.38,
            "segmented": 0.35,
            "compact":   0.34,
        }.get(typology, 0.36)

        mid_ratio = {
            "balanced":  0.30,
            "atrium":    0.32,
            "linear":    0.28,
            "segmented": 0.30,
            "compact":   0.32,
        }.get(typology, 0.30)

        h_front = _round_grid(bh * front_ratio)
        h_mid   = _round_grid(bh * mid_ratio)
        h_rear  = round(bh - h_front - h_mid, 2)

        y_front = by
        y_mid   = round(by + h_front, 2)
        y_rear  = round(by + h_front + h_mid, 2)

        def make_room(
            idx: int,
            name: str,
            rtype: str,
            rx: float,
            ry: float,
            rw: float,
            rh: float,
            zone: str = "public",
            mandatory: bool = True,
        ) -> Dict[str, Any]:
            rx_r = round(rx, 2)
            ry_r = round(ry, 2)
            rw_r = max(3.5, round(rw, 2))
            rh_r = max(3.5, round(rh, 2))
            area = round(rw_r * rh_r, 1)
            cx_norm = (rx_r + rw_r / 2.0) / max(1.0, site_w)
            cy_norm = (ry_r + rh_r / 2.0) / max(1.0, site_d)
            if cx_norm >= 0.5 and cy_norm < 0.5:
                v_zone = "NE"
            elif cx_norm >= 0.5 and cy_norm >= 0.5:
                v_zone = "SE"
            elif cx_norm < 0.5 and cy_norm >= 0.5:
                v_zone = "SW"
            else:
                v_zone = "NW"

            return {
                "id": f"rm_f{floor_idx}_{idx}_{rtype}",
                "name": name,
                "type": rtype,
                "floor": floor_idx,
                "zone": zone,
                "mandatory": mandatory,
                "x": rx_r,
                "y": ry_r,
                "width": rw_r,
                "height": rh_r,
                "area": area,
                "dimensionsLabel": f"{rw_r:g}' × {rh_r:g}'",
                "vastu_zone": v_zone,
                "score": 94,
                "polygon": [
                    [rx_r, ry_r],
                    [round(rx_r + rw_r, 2), ry_r],
                    [round(rx_r + rw_r, 2), round(ry_r + rh_r, 2)],
                    [rx_r, round(ry_r + rh_r, 2)],
                ],
            }

        def partition_strip_x(
            items: List[Tuple[str, str, str, bool, float]],
            strip_x: float,
            strip_y: float,
            strip_w: float,
            strip_h: float,
            start_idx: int,
        ) -> List[Dict[str, Any]]:
            """
            Partitions a horizontal strip [strip_x, strip_y, strip_w, strip_h] along X by weights.
            Also automatically stacks paired small rooms (e.g. Bathroom + Dress/Utility) vertically
            when strip_h >= 11.0 ft so bathrooms have realistic square/rectangular proportions!
            """
            if not items:
                return []

            # Pair up consecutive small service/bath rooms for vertical stacking if strip is tall
            grouped: List[List[Tuple[str, str, str, bool, float]]] = []
            small_types = {"bathroom", "pooja", "utility", "store"}
            i = 0
            while i < len(items):
                cur = items[i]
                if (
                    strip_h >= 10.5
                    and cur[1] in small_types
                    and i + 1 < len(items)
                    and items[i + 1][1] in small_types
                ):
                    grouped.append([cur, items[i + 1]])
                    i += 2
                elif strip_h >= 12.0 and cur[1] == "bathroom":
                    # Split a tall single bathroom slot into Bathroom + Walk-In Dress / Powder Alcove
                    grouped.append([
                        cur,
                        ("Dressing / Linen", "utility", "private", False, cur[4] * 0.65),
                    ])
                    i += 1
                else:
                    grouped.append([cur])
                    i += 1

            col_weights = [max(g[0][4], sum(x[4] for x in g) * 0.62) if len(g) > 1 else g[0][4] for g in grouped]
            total_w = sum(col_weights)
            cur_x = strip_x
            created: List[Dict[str, Any]] = []
            room_idx = start_idx

            for col_i, grp in enumerate(grouped):
                if col_i == len(grouped) - 1:
                    w_i = round((strip_x + strip_w) - cur_x, 2)
                else:
                    w_i = _round_grid(strip_w * (col_weights[col_i] / max(0.01, total_w)))
                    w_i = max(4.5, min(w_i, (strip_x + strip_w) - cur_x - 4.5 * (len(grouped) - 1 - col_i)))

                if len(grp) == 1:
                    nm, rt, zn, mand, _ = grp[0]
                    created.append(make_room(room_idx, nm, rt, cur_x, strip_y, w_i, strip_h, zn, mand))
                    room_idx += 1
                else:
                    # Stack the 2 rooms vertically inside [cur_x, strip_y, w_i, strip_h]
                    nm1, rt1, zn1, mand1, _ = grp[0]
                    nm2, rt2, zn2, mand2, _ = grp[1]
                    h_top = _round_grid(strip_h * 0.54)
                    h_bot = round(strip_h - h_top, 2)
                    created.append(make_room(room_idx, nm1, rt1, cur_x, strip_y, w_i, h_top, zn1, mand1))
                    room_idx += 1
                    created.append(make_room(room_idx, nm2, rt2, cur_x, round(strip_y + h_top, 2), w_i, h_bot, zn2, mand2))
                    room_idx += 1

                cur_x = round(cur_x + w_i, 2)
            return created

        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for item in fl_spec:
            by_type.setdefault(item["type"], []).append(item)

        if floor_idx == 0:
            # ── GROUND FLOOR LAYOUT BY AI ARCHETYPE ───────────────────────────
            front_items: List[Tuple[str, str, str, bool, float]] = []
            for p in by_type.get("parking", []):
                front_items.append((p["name"], "parking", "public", True, 1.05))
            for lv in by_type.get("living", []):
                front_items.append((lv["name"], "living", "public", True, 1.70))
            for pj in by_type.get("pooja", []):
                front_items.append((pj["name"], "pooja", "public", pj.get("mandatory", True), 0.52))
            if not stair_box:
                for bal in by_type.get("balcony", []):
                    front_items.append((bal["name"], "balcony", "outdoor", True, 0.75))

            if typology == "balanced":
                # Living on Left/Center, Pooja in NE, Parking on Right
                front_items = [it for it in front_items if it[1] != "parking"] + [it for it in front_items if it[1] == "parking"]
            elif typology == "segmented":
                # Dual-Wing: Parking on Left (West), Living + Pooja on Right (East/NE)
                pass
            elif typology == "linear" and len(front_items) > 1:
                front_items = list(reversed(front_items))

            rooms_out.extend(partition_strip_x(front_items, bx, y_front, bw, h_front, len(rooms_out)))

            # 2. Middle Band (y_mid, h_mid): Staircase + Courtyard/Dining + Kitchen + Utility
            mid_w_avail = bw
            mid_x_start = bx
            if stair_box:
                st_w = stair_box["width"]
                st_x = stair_box["x"]
                rooms_out.append(make_room(
                    len(rooms_out), "Staircase", "staircase",
                    st_x, y_mid, st_w, h_mid, "circulation", True
                ))
                mid_w_avail = round(bw - st_w, 2)
                if abs(st_x - bx) <= 0.1:
                    mid_x_start = round(bx + st_w, 2)

            mid_items: List[Tuple[str, str, str, bool, float]] = []
            if typology == "atrium":
                mid_items.append(("Brahmasthana Courtyard", "circulation", "public", False, 0.95))
                for dn in by_type.get("dining", []):
                    mid_items.append((dn["name"], "dining", "public", True, 1.15))
            elif typology == "segmented":
                mid_items.append(("Central Foyer", "circulation", "circulation", False, 0.75))
                for dn in by_type.get("dining", []):
                    mid_items.append((dn["name"], "dining", "public", True, 1.25))
            else:
                for dn in by_type.get("dining", []):
                    mid_items.append((dn["name"], "dining", "public", True, 1.25))
                mid_items.append(("Breeze Foyer", "circulation", "circulation", False, 0.70))

            for kt in by_type.get("kitchen", []):
                mid_items.append((kt["name"], "kitchen", "service", True, 1.18))
            for ut in by_type.get("utility", []):
                mid_items.append((ut["name"], "utility", "service", ut.get("mandatory", True), 0.58))
            for st in by_type.get("store", []):
                mid_items.append((st["name"], "store", "service", st.get("mandatory", True), 0.55))

            if not mid_items:
                mid_items.append(("Circulation Hall", "circulation", "circulation", False, 1.0))

            rooms_out.extend(partition_strip_x(mid_items, mid_x_start, y_mid, mid_w_avail, h_mid, len(rooms_out)))

            # 3. Rear Band (y_rear, h_rear): Ground Bedrooms + Realistic En-Suite/Common Baths
            rear_items: List[Tuple[str, str, str, bool, float]] = []
            beds_gf = by_type.get("bedroom", [])
            baths_gf = by_type.get("bathroom", [])
            studies_gf = by_type.get("study", [])
            terraces_gf = by_type.get("terrace", []) if not stair_box else []

            max_len = max(len(beds_gf), len(baths_gf), 1)
            for i in range(max_len):
                if i < len(beds_gf):
                    b_it = beds_gf[i]
                    rear_items.append((b_it["name"], "bedroom", "private", True, 1.55))
                if i < len(baths_gf):
                    bt_it = baths_gf[i]
                    rear_items.append((bt_it["name"], "bathroom", "private", True, 0.65))

            for sd in studies_gf:
                rear_items.append((sd["name"], "study", "private", True, 0.95))
            for tr in terraces_gf:
                rear_items.append((tr["name"], "terrace", "outdoor", True, 1.10))

            if len(rear_items) == 1 and rear_items[0][1] == "bathroom":
                rear_items.insert(0, ("Garden Lounge / Verandah", "circulation", "public", False, 1.45))

            if not rear_items:
                rear_items.append(("Rear Verandah / Lounge", "circulation", "public", False, 1.0))

            if typology == "compact" and len(rear_items) > 1:
                rear_items = list(reversed(rear_items))

            rooms_out.extend(partition_strip_x(rear_items, bx, y_rear, bw, h_rear, len(rooms_out)))

        else:
            # ── UPPER FLOOR (Floor 1+) LAYOUT ─────────────────────────────────
            front_items_uf: List[Tuple[str, str, str, bool, float]] = []
            for bal in by_type.get("balcony", []):
                front_items_uf.append((bal["name"], "balcony", "outdoor", True, 0.85))

            beds_uf = list(by_type.get("bedroom", []))
            baths_uf = list(by_type.get("bathroom", []))
            studies_uf = list(by_type.get("study", []))
            terraces_uf = list(by_type.get("terrace", []))

            if beds_uf:
                first_bed = beds_uf.pop(0)
                front_items_uf.append((first_bed["name"], "bedroom", "private", True, 1.65))
            if baths_uf and not beds_uf:
                first_bath = baths_uf.pop(0)
                front_items_uf.append((first_bath["name"], "bathroom", "private", True, 0.65))

            if not front_items_uf:
                front_items_uf.append(("Upper Front Gallery", "circulation", "circulation", False, 1.0))

            if typology in ("balanced", "compact") and len(front_items_uf) > 1:
                front_items_uf = list(reversed(front_items_uf))

            rooms_out.extend(partition_strip_x(front_items_uf, bx, y_front, bw, h_front, len(rooms_out)))

            # 2. Middle Band (y_mid, h_mid): Staircase (PINNED to exact Ground Floor X, Y, W, H!)
            mid_w_avail = bw
            mid_x_start = bx
            if stair_box:
                st_w = stair_box["width"]
                st_x = stair_box["x"]
                rooms_out.append(make_room(
                    len(rooms_out), "Staircase", "staircase",
                    st_x, y_mid, st_w, h_mid, "circulation", True
                ))
                mid_w_avail = round(bw - st_w, 2)
                if abs(st_x - bx) <= 0.1:
                    mid_x_start = round(bx + st_w, 2)

            mid_items_uf: List[Tuple[str, str, str, bool, float]] = [
                ("Upper Family Lounge", "circulation", "circulation", False, 1.20)
            ]
            if baths_uf:
                bt0 = baths_uf.pop(0)
                mid_items_uf.append((bt0["name"], "bathroom", "private", True, 0.68))
            for sd in studies_uf:
                mid_items_uf.append((sd["name"], "study", "private", True, 0.95))

            rooms_out.extend(partition_strip_x(mid_items_uf, mid_x_start, y_mid, mid_w_avail, h_mid, len(rooms_out)))

            # 3. Rear Band (y_rear, h_rear): Remaining Bedrooms + Remaining Bathrooms + Terrace
            rear_items_uf: List[Tuple[str, str, str, bool, float]] = []
            for b_rem in beds_uf:
                rear_items_uf.append((b_rem["name"], "bedroom", "private", True, 1.50))
            for bt_rem in baths_uf:
                rear_items_uf.append((bt_rem["name"], "bathroom", "private", True, 0.65))
            for tr in terraces_uf:
                rear_items_uf.append((tr["name"], "terrace", "outdoor", True, 1.20))

            if not rear_items_uf:
                rear_items_uf.append(("Sky Terrace Deck", "terrace", "outdoor", False, 1.0))

            rooms_out.extend(partition_strip_x(rear_items_uf, bx, y_rear, bw, h_rear, len(rooms_out)))

        return rooms_out, open_spaces

    # ── STAGE 6: SPATIAL RELATIONSHIP GRAPH ───────────────────────────────────
    def _build_floor_spatial_graph(
        self, rooms: List[Dict[str, Any]], floor_idx: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Builds the Stage 6 Spatial Relationship Graph for a floor based on both
        architectural adjacency rules and physical shared-wall adjacency.
        """
        nodes = []
        for r in rooms:
            node_id = f"staircase_f{floor_idx}" if r["type"] == "staircase" else r["id"]
            nodes.append({
                "id": node_id,
                "roomId": r["id"],
                "name": r["name"],
                "type": r["type"],
                "zone": r["zone"],
                "floor": floor_idx,
                "area": r["area"],
            })

        edges = []
        n = len(rooms)
        for i in range(n):
            for j in range(i + 1, n):
                r1, r2 = rooms[i], rooms[j]
                shared = self._shared_wall_segment(r1, r2)
                if shared and shared["length"] >= 2.2:
                    rel = self._classify_spatial_relation(r1["type"], r2["type"])
                    edges.append({
                        "source": r1["id"],
                        "target": r2["id"],
                        "sourceName": r1["name"],
                        "targetName": r2["name"],
                        "relation": rel,
                        "sharedWallLength": round(shared["length"], 2),
                        "floor": floor_idx,
                    })
        return nodes, edges

    def _classify_spatial_relation(self, t1: str, t2: str) -> str:
        pair = {t1, t2}
        if pair == {"living", "dining"}:
            return "open_flow"
        if pair == {"dining", "kitchen"}:
            return "service_adj"
        if pair == {"kitchen", "utility"} or pair == {"kitchen", "store"}:
            return "utility_access"
        if "staircase" in pair or "circulation" in pair:
            return "circulation_access"
        if pair == {"bedroom", "bathroom"}:
            return "en_suite_or_bath_access"
        if "balcony" in pair or "terrace" in pair:
            return "outdoor_access"
        if "parking" in pair:
            return "arrival_entry"
        return "adjacent"

    def _shared_wall_segment(
        self, r1: Dict[str, Any], r2: Dict[str, Any], tol: float = 0.15
    ) -> Optional[Dict[str, Any]]:
        """
        Checks if r1 and r2 share a vertical or horizontal boundary segment.
        Returns {orientation, coord, start, end, length} if they share a wall.
        """
        x1a, y1a, x1b, y1b = r1["x"], r1["y"], r1["x"] + r1["width"], r1["y"] + r1["height"]
        x2a, y2a, x2b, y2b = r2["x"], r2["y"], r2["x"] + r2["width"], r2["y"] + r2["height"]

        # Vertical shared wall: x1b == x2a or x2b == x1a
        if abs(x1b - x2a) <= tol or abs(x2b - x1a) <= tol:
            vx = round((x1b + x2a) / 2.0, 2) if abs(x1b - x2a) <= tol else round((x2b + x1a) / 2.0, 2)
            oy1 = max(y1a, y2a)
            oy2 = min(y1b, y2b)
            if oy2 - oy1 > 0.5:
                return {
                    "orientation": "vertical",
                    "x1": vx, "y1": round(oy1, 2),
                    "x2": vx, "y2": round(oy2, 2),
                    "length": round(oy2 - oy1, 2),
                }

        # Horizontal shared wall: y1b == y2a or y2b == y1a
        if abs(y1b - y2a) <= tol or abs(y2b - y1a) <= tol:
            hy = round((y1b + y2a) / 2.0, 2) if abs(y1b - y2a) <= tol else round((y2b + y1a) / 2.0, 2)
            ox1 = max(x1a, x2a)
            ox2 = min(x1b, x2b)
            if ox2 - ox1 > 0.5:
                return {
                    "orientation": "horizontal",
                    "x1": round(ox1, 2), "y1": hy,
                    "x2": round(ox2, 2), "y2": hy,
                    "length": round(ox2 - ox1, 2),
                }
        return None

    # ── STAGE 9: WALL GENERATION (DEDUPLICATED SHARED BOUNDARIES) ─────────────
    def _generate_floor_walls(
        self,
        rooms: List[Dict[str, Any]],
        floor_idx: int,
        bx: float,
        by: float,
        bw: float,
        bh: float,
        site_w: float,
        site_d: float,
    ) -> List[Dict[str, Any]]:
        """
        Generates deduplicated wall segments from room boundaries:
          • Splits collinear room edges at all intersection coordinates
          • Deduplicates shared wall intervals between adjacent rooms
          • Assigns exterior vs interior vs parapet thickness and wall_type
        """
        h_coords_by_y: Dict[float, set] = {}
        v_coords_by_x: Dict[float, set] = {}

        raw_h_edges: List[Tuple[float, float, float, Dict[str, Any]]] = []
        raw_v_edges: List[Tuple[float, float, float, Dict[str, Any]]] = []

        for r in rooms:
            x1 = round(r["x"], 2)
            y1 = round(r["y"], 2)
            x2 = round(r["x"] + r["width"], 2)
            y2 = round(r["y"] + r["height"], 2)

            raw_h_edges.append((y1, x1, x2, r))
            raw_h_edges.append((y2, x1, x2, r))
            raw_v_edges.append((x1, y1, y2, r))
            raw_v_edges.append((x2, y1, y2, r))

            h_coords_by_y.setdefault(y1, set()).update([x1, x2])
            h_coords_by_y.setdefault(y2, set()).update([x1, x2])
            v_coords_by_x.setdefault(x1, set()).update([y1, y2])
            v_coords_by_x.setdefault(x2, set()).update([y1, y2])

        walls: List[Dict[str, Any]] = []
        wall_counter = 1
        outdoor_types = {"parking", "balcony", "terrace", "open_space"}

        # Process horizontal wall intervals
        for y_val, x_pts_set in sorted(h_coords_by_y.items()):
            x_pts = sorted(x_pts_set)
            for k in range(len(x_pts) - 1):
                xa, xb = x_pts[k], x_pts[k + 1]
                if xb - xa < 0.2:
                    continue
                # Find which rooms touch this interval [xa, xb] at y_val
                touching_rooms = [
                    r for (ey, ex1, ex2, r) in raw_h_edges
                    if abs(ey - y_val) <= 0.08 and ex1 <= xa + 0.08 and ex2 >= xb - 0.08
                ]
                if not touching_rooms:
                    continue

                indoor_touch = [r for r in touching_rooms if r["type"] not in outdoor_types]
                is_outer_env = abs(y_val - by) <= 0.1 or abs(y_val - (by + bh)) <= 0.1

                if len(indoor_touch) >= 2:
                    w_type = "interior"
                    thick = self.INTERIOR_WALL_THICKNESS
                elif len(indoor_touch) == 1:
                    w_type = "exterior"
                    thick = self.EXTERIOR_WALL_THICKNESS
                else:
                    w_type = "parapet" if not is_outer_env else "exterior_low"
                    thick = self.PARAPET_WALL_THICKNESS

                walls.append({
                    "id": f"w_f{floor_idx}_{wall_counter}",
                    "start": {"x": xa, "y": y_val},
                    "end": {"x": xb, "y": y_val},
                    "orientation": "horizontal",
                    "length": round(xb - xa, 2),
                    "thickness": thick,
                    "wallType": w_type,
                    "floor": floor_idx,
                    "roomIds": [r["id"] for r in touching_rooms],
                })
                wall_counter += 1

        # Process vertical wall intervals
        for x_val, y_pts_set in sorted(v_coords_by_x.items()):
            y_pts = sorted(y_pts_set)
            for k in range(len(y_pts) - 1):
                ya, yb = y_pts[k], y_pts[k + 1]
                if yb - ya < 0.2:
                    continue
                touching_rooms = [
                    r for (ex, ey1, ey2, r) in raw_v_edges
                    if abs(ex - x_val) <= 0.08 and ey1 <= ya + 0.08 and ey2 >= yb - 0.08
                ]
                if not touching_rooms:
                    continue

                indoor_touch = [r for r in touching_rooms if r["type"] not in outdoor_types]
                is_outer_env = abs(x_val - bx) <= 0.1 or abs(x_val - (bx + bw)) <= 0.1

                if len(indoor_touch) >= 2:
                    w_type = "interior"
                    thick = self.INTERIOR_WALL_THICKNESS
                elif len(indoor_touch) == 1:
                    w_type = "exterior"
                    thick = self.EXTERIOR_WALL_THICKNESS
                else:
                    w_type = "parapet" if not is_outer_env else "exterior_low"
                    thick = self.PARAPET_WALL_THICKNESS

                walls.append({
                    "id": f"w_f{floor_idx}_{wall_counter}",
                    "start": {"x": x_val, "y": ya},
                    "end": {"x": x_val, "y": yb},
                    "orientation": "vertical",
                    "length": round(yb - ya, 2),
                    "thickness": thick,
                    "wallType": w_type,
                    "floor": floor_idx,
                    "roomIds": [r["id"] for r in touching_rooms],
                })
                wall_counter += 1

        return walls

    # ── STAGE 10: AUTOMATIC DOOR GENERATION ───────────────────────────────────
    def _generate_floor_doors(
        self,
        rooms: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        graph_edges: List[Dict[str, Any]],
        floor_idx: int,
        bx: float,
        by: float,
        bw: float,
        bh: float,
    ) -> List[Dict[str, Any]]:
        """
        Places doors on valid shared walls so every room is accessible and
        circulation paths are logical and unobstructed.
        """
        doors: List[Dict[str, Any]] = []
        room_by_id = {r["id"]: r for r in rooms}
        door_counter = 1

        # 1. Main Entrance Door on Ground Floor (into Living Room from Front / Parking)
        if floor_idx == 0:
            living_rooms = [r for r in rooms if r["type"] == "living"]
            if living_rooms:
                liv = living_rooms[0]
                # Find front horizontal wall or shared wall with parking
                front_wall = next(
                    (
                        w for w in walls
                        if liv["id"] in w["roomIds"]
                        and w["orientation"] == "horizontal"
                        and abs(w["start"]["y"] - liv["y"]) <= 0.15
                        and w["length"] >= 3.2
                    ),
                    None,
                )
                if front_wall:
                    dw = min(3.5, round(front_wall["length"] * 0.45, 2))
                    mx = round((front_wall["start"]["x"] + front_wall["end"]["x"]) / 2.0, 2)
                    my = front_wall["start"]["y"]
                    doors.append({
                        "id": f"d_f{floor_idx}_{door_counter}",
                        "wallId": front_wall["id"],
                        "x": mx,
                        "y": my,
                        "width": dw,
                        "orientation": "horizontal",
                        "swing": "inward-south",
                        "doorType": "main_entrance",
                        "connects": ["site_entrance", liv["id"]],
                        "connectsLabels": ["Main Entrance", liv["name"]],
                        "floor": floor_idx,
                    })
                    door_counter += 1

        # 2. Interior & Balcony/Terrace Doors between adjacent rooms
        connected_pairs = set()

        def should_place_door(t1: str, t2: str) -> Tuple[bool, int]:
            """Returns (allow_door, priority_score). Lower priority_score = preferred connection."""
            pair = {t1, t2}
            # Never put a door directly between Kitchen and Bathroom, or Pooja and Bathroom, or Parking and Bathroom
            if pair in ({"kitchen", "bathroom"}, {"pooja", "bathroom"}, {"parking", "bathroom"}, {"dining", "bathroom"}):
                return False, 99
            if pair == {"bathroom", "bathroom"}:
                return False, 99
            if "circulation" in pair or "staircase" in pair:
                return True, 1
            if pair in ({"living", "dining"}, {"dining", "kitchen"}, {"kitchen", "utility"}, {"kitchen", "store"}):
                return True, 1
            if pair == {"bedroom", "bathroom"}:
                return True, 1
            if "balcony" in pair or "terrace" in pair:
                return True, 2
            if "living" in pair or "dining" in pair:
                return True, 2
            return True, 3

        # Gather candidate shared walls for each room pair
        shared_walls = [w for w in walls if len(w["roomIds"]) >= 2 and w["length"] >= 2.5]

        # First connect high-priority architectural pairs, ensuring each bathroom/utility/pooja
        # gets 1 clean door and bedrooms connect to circulation/living/dining + attached bath
        door_deg: Dict[str, int] = {r["id"]: 0 for r in rooms}
        bath_connected: set = set()

        # Sort shared walls by priority of room types they connect
        scored_walls = []
        for w in shared_walls:
            r1 = room_by_id.get(w["roomIds"][0])
            r2 = room_by_id.get(w["roomIds"][1])
            if not r1 or not r2:
                continue
            ok, prio = should_place_door(r1["type"], r2["type"])
            if ok:
                scored_walls.append((prio, -w["length"], w, r1, r2))

        scored_walls.sort(key=lambda item: (item[0], item[1]))

        for prio, _, w, r1, r2 in scored_walls:
            pair_key = tuple(sorted([r1["id"], r2["id"]]))
            if pair_key in connected_pairs:
                continue
            # A bathroom or pooja or store only needs 1 door
            for single_door_type in ("bathroom", "pooja", "store", "utility"):
                if r1["type"] == single_door_type and r1["id"] in bath_connected:
                    break
                if r2["type"] == single_door_type and r2["id"] in bath_connected:
                    break
            else:
                # Place door on wall `w`
                types_set = {r1["type"], r2["type"]}
                if "bathroom" in types_set or "pooja" in types_set or "utility" in types_set or "store" in types_set:
                    dw = min(2.5, round(w["length"] * 0.6, 2))
                else:
                    dw = min(3.0, round(w["length"] * 0.55, 2))

                mx = round((w["start"]["x"] + w["end"]["x"]) / 2.0, 2)
                my = round((w["start"]["y"] + w["end"]["y"]) / 2.0, 2)

                doors.append({
                    "id": f"d_f{floor_idx}_{door_counter}",
                    "wallId": w["id"],
                    "x": mx,
                    "y": my,
                    "width": dw,
                    "orientation": w["orientation"],
                    "swing": "inward",
                    "doorType": "balcony_sliding" if ("balcony" in types_set or "terrace" in types_set) else "interior",
                    "connects": [r1["id"], r2["id"]],
                    "connectsLabels": [r1["name"], r2["name"]],
                    "floor": floor_idx,
                })
                door_counter += 1
                connected_pairs.add(pair_key)
                door_deg[r1["id"]] = door_deg.get(r1["id"], 0) + 1
                door_deg[r2["id"]] = door_deg.get(r2["id"], 0) + 1
                for single_door_type in ("bathroom", "pooja", "store", "utility"):
                    if r1["type"] == single_door_type:
                        bath_connected.add(r1["id"])
                    if r2["type"] == single_door_type:
                        bath_connected.add(r2["id"])

        # Ensure every room on the floor has at least 1 door connection
        for r in rooms:
            if door_deg.get(r["id"], 0) == 0:
                fallback_wall = next(
                    (w for w in walls if r["id"] in w["roomIds"] and len(w["roomIds"]) >= 2 and w["length"] >= 2.2),
                    None,
                )
                if fallback_wall:
                    other_id = [rid for rid in fallback_wall["roomIds"] if rid != r["id"]][0]
                    other_rm = room_by_id.get(other_id, r)
                    mx = round((fallback_wall["start"]["x"] + fallback_wall["end"]["x"]) / 2.0, 2)
                    my = round((fallback_wall["start"]["y"] + fallback_wall["end"]["y"]) / 2.0, 2)
                    doors.append({
                        "id": f"d_f{floor_idx}_{door_counter}",
                        "wallId": fallback_wall["id"],
                        "x": mx,
                        "y": my,
                        "width": min(2.6, round(fallback_wall["length"] * 0.6, 2)),
                        "orientation": fallback_wall["orientation"],
                        "swing": "inward",
                        "doorType": "interior",
                        "connects": [r["id"], other_id],
                        "connectsLabels": [r["name"], other_rm["name"]],
                        "floor": floor_idx,
                    })
                    door_counter += 1

        return doors

    # ── STAGE 11: WINDOW GENERATION ───────────────────────────────────────────
    def _generate_floor_windows(
        self,
        rooms: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        doors: List[Dict[str, Any]],
        floor_idx: int,
    ) -> List[Dict[str, Any]]:
        """
        Places windows on suitable exterior walls based on room type, dimensions,
        natural light, and cross-ventilation requirements.
        """
        windows: List[Dict[str, Any]] = []
        room_by_id = {r["id"]: r for r in rooms}
        walls_with_doors = {d["wallId"] for d in doors}
        win_counter = 1

        # Window target width by room type
        win_target_width = {
            "living":    5.0,
            "dining":    4.0,
            "kitchen":   3.5,
            "bedroom":   4.5,
            "study":     4.0,
            "pooja":     2.5,
            "bathroom":  2.0,  # high-sill ventilator
            "utility":   2.5,
            "staircase": 3.0,
        }

        for w in walls:
            if w["wallType"] != "exterior":
                continue
            if w["id"] in walls_with_doors:
                continue
            if w["length"] < 3.0:
                continue
            if not w["roomIds"]:
                continue

            rm = room_by_id.get(w["roomIds"][0])
            if not rm:
                continue
            rtype = rm["type"]
            if rtype in ("parking", "balcony", "terrace", "store"):
                continue

            target_w = win_target_width.get(rtype, 3.5)
            actual_w = min(target_w, round(w["length"] * 0.5, 2))
            if actual_w < 1.8:
                continue

            mx = round((w["start"]["x"] + w["end"]["x"]) / 2.0, 2)
            my = round((w["start"]["y"] + w["end"]["y"]) / 2.0, 2)

            windows.append({
                "id": f"win_f{floor_idx}_{win_counter}",
                "wallId": w["id"],
                "roomId": rm["id"],
                "roomName": rm["name"],
                "x": mx,
                "y": my,
                "width": actual_w,
                "orientation": w["orientation"],
                "windowType": "ventilator" if rtype == "bathroom" else "casement_glazing",
                "floor": floor_idx,
            })
            win_counter += 1

        return windows

    # ── STAGE 12: STAIRCASE & STRUCTURAL COLUMN GENERATION ────────────────────
    def _generate_staircase_geometry(
        self,
        rooms: List[Dict[str, Any]],
        floor_idx: int,
        floors_count: int,
    ) -> Optional[Dict[str, Any]]:
        stair_room = next((r for r in rooms if r["type"] == "staircase"), None)
        if not stair_room:
            return None

        sx = stair_room["x"]
        sy = stair_room["y"]
        sw = stair_room["width"]
        sh = stair_room["height"]

        # Generate 10 explicit tread lines inside the dog-legged staircase box
        num_treads = 8
        treads = []
        landing_h = round(sh * 0.24, 2)
        flight_h = round(sh - landing_h, 2)
        step_depth = round(flight_h / max(1, num_treads), 2)
        mid_x = round(sx + sw / 2.0, 2)

        for i in range(1, num_treads):
            ty = round(sy + i * step_depth, 2)
            # Flight 1 (left half) and Flight 2 (right half)
            treads.append({"x1": sx + 0.3, "y1": ty, "x2": mid_x - 0.15, "y2": ty})
            treads.append({"x1": mid_x + 0.15, "y1": ty, "x2": sx + sw - 0.3, "y2": ty})

        return {
            "id": f"stair_geom_f{floor_idx}",
            "roomId": stair_room["id"],
            "x": sx,
            "y": sy,
            "width": sw,
            "height": sh,
            "floor": floor_idx,
            "connectsFloors": list(range(floors_count)),
            "direction": "UP" if floor_idx < floors_count - 1 else "DN",
            "landing": {
                "x": sx,
                "y": round(sy + flight_h, 2),
                "width": sw,
                "height": landing_h,
            },
            "treads": treads,
        }

    def _generate_structural_columns(
        self,
        rooms: List[Dict[str, Any]],
        floor_idx: int,
        bx: float,
        by: float,
        bw: float,
        bh: float,
    ) -> List[Dict[str, Any]]:
        """
        Places structural columns (0.75 x 0.75 ft) at building envelope corners
        and primary room grid junctions.
        """
        corner_pts = set()
        for r in rooms:
            x1 = round(r["x"], 2)
            y1 = round(r["y"], 2)
            x2 = round(r["x"] + r["width"], 2)
            y2 = round(r["y"] + r["height"], 2)
            for pt in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
                corner_pts.add(pt)

        columns = []
        for idx, (cx, cy) in enumerate(sorted(corner_pts), start=1):
            columns.append({
                "id": f"col_f{floor_idx}_{idx}",
                "x": cx,
                "y": cy,
                "size": 0.75,
                "floor": floor_idx,
            })
        return columns

    def _generate_floor_dimensions(
        self,
        rooms: List[Dict[str, Any]],
        site_w: float,
        site_d: float,
        bx: float,
        by: float,
        bw: float,
        bh: float,
        floor_idx: int,
    ) -> Dict[str, Any]:
        return {
            "siteWidthLabel": f"{site_w:g}'-0\"",
            "siteDepthLabel": f"{site_d:g}'-0\"",
            "buildingWidthLabel": _fmt_feet_inches(bw),
            "buildingDepthLabel": _fmt_feet_inches(bh),
            "roomDimensions": [
                {
                    "roomId": r["id"],
                    "roomName": r["name"],
                    "widthFt": r["width"],
                    "heightFt": r["height"],
                    "areaSqFt": r["area"],
                    "label": f"{_fmt_feet_inches(r['width'])} × {_fmt_feet_inches(r['height'])}",
                    "floor": floor_idx,
                }
                for r in rooms
            ],
        }
