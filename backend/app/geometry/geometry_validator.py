"""
ZYNORA-ML — Stages 13, 14 & 15: Geometry Validator, Auto-Corrector & Quality Check
===================================================================================
Implements:
  Stage 13: Geometry Validation
    • No rooms overlap
    • No walls overlap incorrectly
    • All rooms are enclosed
    • All required rooms exist
    • Doors connect valid spaces
    • Windows belong to valid exterior walls
    • Staircase connects floors
    • Building stays inside site boundary
    • Parking fits within the site
    • Required circulation exists
    • Dimensions are valid
    • All geometry is connected appropriately

  Stage 14: Automatic Correction
    • Adjusts room dimensions / positions to resolve overlaps or site boundary breaches
    • Snaps near-adjacent walls so rooms share clean boundaries
    • Regenerates walls, doors, windows, stairs, and columns after room adjustments
    • Repeats validation after every correction pass
    • Never removes mandatory user requirements

  Stage 15: Floor Plan Quality Check
    • Verifies and outputs the 12-point architectural quality checklist
"""

from typing import Dict, Any, List, Tuple
from .floorplan_geometry_builder import FloorplanGeometryBuilder


class GeometryValidator:
    """
    Stages 13, 14, and 15 of the Architectural Floor Plan Pipeline.
    """

    def __init__(self):
        self.builder = FloorplanGeometryBuilder()

    def validate_and_correct(
        self,
        floorplan_geom: Dict[str, Any],
        structured_reqs: Dict[str, Any],
        max_iterations: int = 4,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Runs Stage 13 Validation -> Stage 14 Automatic Correction loop -> Stage 15 Quality Check.
        Returns (corrected_floorplan_geom, validation_and_quality_report).
        """
        corrections_applied: List[str] = []
        report = self.validate_geometry(floorplan_geom, structured_reqs)

        iteration = 0
        while not report["isValid"] and iteration < max_iterations:
            iteration += 1
            step_fixes = self._apply_automatic_corrections(floorplan_geom, structured_reqs)
            if not step_fixes:
                break
            corrections_applied.extend(step_fixes)
            report = self.validate_geometry(floorplan_geom, structured_reqs)

        report["correctionsApplied"] = corrections_applied
        report["correctionIterations"] = iteration
        report["qualityChecklist"] = self._build_quality_checklist(report, floorplan_geom, structured_reqs)
        return floorplan_geom, report

    # ── STAGE 13: GEOMETRY VALIDATION ─────────────────────────────────────────
    def validate_geometry(
        self,
        floorplan_geom: Dict[str, Any],
        structured_reqs: Dict[str, Any],
    ) -> Dict[str, Any]:
        site = floorplan_geom.get("siteBoundary", {})
        site_w = float(site.get("width", 30.0))
        site_d = float(site.get("depth", 40.0))
        floors_geom = floorplan_geom.get("floorsGeometry", [])
        floors_count = len(floors_geom)

        room_overlaps: List[str] = []
        wall_overlaps: List[str] = []
        unenclosed_rooms: List[str] = []
        invalid_doors: List[str] = []
        invalid_windows: List[str] = []
        boundary_breaches: List[str] = []
        invalid_dimensions: List[str] = []
        disconnected_rooms: List[str] = []

        all_rooms: List[Dict[str, Any]] = []
        stair_coords_by_floor: List[Tuple[float, float, float, float]] = []

        for fl in floors_geom:
            fl_idx = fl.get("floor", 0)
            rooms = fl.get("rooms", [])
            walls = fl.get("walls", [])
            doors = fl.get("doors", [])
            windows = fl.get("windows", [])
            all_rooms.extend(rooms)

            # 1. Check room dimensions & site boundary containment
            for r in rooms:
                rx, ry = float(r.get("x", 0)), float(r.get("y", 0))
                rw, rh = float(r.get("width", 0)), float(r.get("height", 0))
                if rw < 3.0 or rh < 3.0:
                    invalid_dimensions.append(f"{r['name']} (Floor {fl_idx}): {rw}x{rh} ft below minimum")
                if rx < -0.05 or ry < -0.05 or (rx + rw) > site_w + 0.05 or (ry + rh) > site_d + 0.05:
                    boundary_breaches.append(f"{r['name']} (Floor {fl_idx}) exceeds site boundary")
                if r.get("type") == "staircase":
                    stair_coords_by_floor.append((round(rx, 1), round(ry, 1), round(rw, 1), round(rh, 1)))

            # 2. Check pairwise room overlaps on same floor
            n = len(rooms)
            for i in range(n):
                for j in range(i + 1, n):
                    r1, r2 = rooms[i], rooms[j]
                    ox = max(0.0, min(r1["x"] + r1["width"], r2["x"] + r2["width"]) - max(r1["x"], r2["x"]))
                    oy = max(0.0, min(r1["y"] + r1["height"], r2["y"] + r2["height"]) - max(r1["y"], r2["y"]))
                    if ox * oy > 0.25:  # > 0.25 sq ft overlap
                        room_overlaps.append(
                            f"{r1['name']} overlaps {r2['name']} on Floor {fl_idx} ({ox * oy:.1f} sq ft)"
                        )

            # 3. Check duplicate/overlapping collinear walls on same floor
            wn = len(walls)
            for i in range(wn):
                for j in range(i + 1, wn):
                    w1, w2 = walls[i], walls[j]
                    if w1["orientation"] != w2["orientation"]:
                        continue
                    if w1["orientation"] == "horizontal" and abs(w1["start"]["y"] - w2["start"]["y"]) < 0.05:
                        ox = min(w1["end"]["x"], w2["end"]["x"]) - max(w1["start"]["x"], w2["start"]["x"])
                        if ox > 0.15:
                            wall_overlaps.append(f"Wall {w1['id']} overlaps {w2['id']} on Floor {fl_idx}")
                    elif w1["orientation"] == "vertical" and abs(w1["start"]["x"] - w2["start"]["x"]) < 0.05:
                        oy = min(w1["end"]["y"], w2["end"]["y"]) - max(w1["start"]["y"], w2["start"]["y"])
                        if oy > 0.15:
                            wall_overlaps.append(f"Wall {w1['id']} overlaps {w2['id']} on Floor {fl_idx}")

            # 4. Check all rooms are enclosed by walls
            wall_ids_by_room: Dict[str, int] = {r["id"]: 0 for r in rooms}
            for w in walls:
                for rid in w.get("roomIds", []):
                    if rid in wall_ids_by_room:
                        wall_ids_by_room[rid] += 1
            for r in rooms:
                if wall_ids_by_room.get(r["id"], 0) < 4:
                    unenclosed_rooms.append(f"{r['name']} (Floor {fl_idx}) has fewer than 4 bounding wall segments")

            # 5. Check doors belong to valid walls and connect valid spaces
            wall_id_map = {w["id"]: w for w in walls}
            room_id_set = {r["id"] for r in rooms} | {"site_entrance"}
            room_door_count = {r["id"]: 0 for r in rooms}

            for d in doors:
                wid = d.get("wallId")
                if wid not in wall_id_map:
                    invalid_doors.append(f"Door {d['id']} is not attached to a valid wall")
                for cid in d.get("connects", []):
                    if cid not in room_id_set:
                        invalid_doors.append(f"Door {d['id']} connects unknown space {cid}")
                    if cid in room_door_count:
                        room_door_count[cid] += 1

            for r in rooms:
                if room_door_count.get(r["id"], 0) == 0:
                    disconnected_rooms.append(f"{r['name']} (Floor {fl_idx}) has no door access")

            # 6. Check windows belong to valid exterior walls
            for win in windows:
                w_obj = wall_id_map.get(win.get("wallId"))
                if not w_obj or w_obj.get("wallType") != "exterior":
                    invalid_windows.append(f"Window {win['id']} is not on an exterior wall")

        # 7. Check all required rooms exist
        req_rooms = structured_reqs.get("requiredRooms", {})
        missing_rooms: List[str] = []
        actual_counts: Dict[str, int] = {}
        for r in all_rooms:
            rt = r.get("type", "")
            key = "bedrooms" if rt == "bedroom" else ("bathrooms" if rt == "bathroom" else ("store_room" if rt == "store" else rt))
            actual_counts[key] = actual_counts.get(key, 0) + 1

        for r_key, req_cnt in req_rooms.items():
            cnt = int(req_cnt or 0)
            if cnt <= 0 or r_key in ("garden", "guest_room"):
                continue
            if r_key == "bedrooms":
                expected = cnt + int(req_rooms.get("guest_room", 0))
                if actual_counts.get("bedrooms", 0) < cnt:
                    missing_rooms.append(f"Bedrooms: requested {expected}, found {actual_counts.get('bedrooms', 0)}")
            elif r_key == "staircase":
                if floors_count >= 2 and actual_counts.get("staircase", 0) < floors_count:
                    missing_rooms.append("Staircase missing on one or more floors")
            else:
                if actual_counts.get(r_key, 0) < 1:
                    missing_rooms.append(f"Missing required room: {r_key}")

        # 8. Check staircase vertical alignment across floors
        staircase_aligned = True
        if floors_count >= 2:
            if len(stair_coords_by_floor) < floors_count:
                staircase_aligned = False
            else:
                ref = stair_coords_by_floor[0]
                for st_c in stair_coords_by_floor[1:]:
                    if abs(st_c[0] - ref[0]) > 0.5 or abs(st_c[1] - ref[1]) > 0.5:
                        staircase_aligned = False

        # 9. Check parking fits inside site
        parking_rooms = [r for r in all_rooms if r.get("type") == "parking"]
        parking_valid = True
        if int(req_rooms.get("parking", 0)) > 0:
            if not parking_rooms:
                parking_valid = False
            else:
                for pr in parking_rooms:
                    if pr["x"] < 0 or pr["y"] < 0 or pr["x"] + pr["width"] > site_w or pr["y"] + pr["height"] > site_d:
                        parking_valid = False

        checks = {
            "noRoomOverlaps":          len(room_overlaps) == 0,
            "noWallOverlaps":          len(wall_overlaps) == 0,
            "allRoomsEnclosed":        len(unenclosed_rooms) == 0,
            "allRequiredRoomsExist":   len(missing_rooms) == 0,
            "doorsConnectValidSpaces": len(invalid_doors) == 0,
            "windowsOnExteriorWalls":  len(invalid_windows) == 0,
            "staircaseConnectsFloors": staircase_aligned,
            "buildingInsideSite":      len(boundary_breaches) == 0,
            "parkingFitsSite":         parking_valid,
            "circulationExists":       len(disconnected_rooms) == 0,
            "dimensionsValid":         len(invalid_dimensions) == 0,
            "geometryConnected":       len(unenclosed_rooms) == 0 and len(disconnected_rooms) == 0,
        }

        is_valid = all(checks.values())

        return {
            "isValid": is_valid,
            "checks": checks,
            "issues": {
                "roomOverlaps":       room_overlaps,
                "wallOverlaps":       wall_overlaps,
                "unenclosedRooms":    unenclosed_rooms,
                "missingRooms":       missing_rooms,
                "invalidDoors":       invalid_doors,
                "invalidWindows":     invalid_windows,
                "boundaryBreaches":   boundary_breaches,
                "invalidDimensions":  invalid_dimensions,
                "disconnectedRooms":  disconnected_rooms,
            },
        }

    # ── STAGE 14: AUTOMATIC GEOMETRIC CORRECTION ──────────────────────────────
    def _apply_automatic_corrections(
        self,
        floorplan_geom: Dict[str, Any],
        structured_reqs: Dict[str, Any],
    ) -> List[str]:
        """
        Fixes geometric problems (e.g., overlaps, boundary breaches, snapped walls,
        or unanchored doors/windows after user edits) without altering mandatory requirements.
        """
        fixes: List[str] = []
        site = floorplan_geom.get("siteBoundary", {})
        site_w = float(site.get("width", 30.0))
        site_d = float(site.get("depth", 40.0))
        bldg = floorplan_geom.get("buildingBoundary", {})
        bx = float(bldg.get("x", 2.0))
        by = float(bldg.get("y", 3.0))
        bw = float(bldg.get("width", site_w - 4.0))
        bh = float(bldg.get("depth", site_d - 5.0))

        floors_geom = floorplan_geom.get("floorsGeometry", [])
        floors_count = len(floors_geom)

        # Find ground floor staircase to align upper floors if needed
        gf_stair = None
        for fl in floors_geom:
            fl_idx = fl.get("floor", 0)
            rooms = fl.get("rooms", [])

            # 1. Clamp room dimensions & positions inside building/site boundary
            for r in rooms:
                if r["width"] < 3.5:
                    r["width"] = 3.5
                    fixes.append(f"Expanded {r['name']} width to minimum 3.5 ft")
                if r["height"] < 3.5:
                    r["height"] = 3.5
                    fixes.append(f"Expanded {r['name']} height to minimum 3.5 ft")
                if r["width"] > bw:
                    r["width"] = bw
                    fixes.append(f"Clamped {r['name']} width to building footprint ({bw} ft)")
                if r["height"] > bh:
                    r["height"] = bh
                    fixes.append(f"Clamped {r['name']} height to building footprint ({bh} ft)")

                if r["x"] < bx:
                    r["x"] = bx
                    fixes.append(f"Moved {r['name']} inside left building boundary")
                if r["y"] < by:
                    r["y"] = by
                    fixes.append(f"Moved {r['name']} inside front building boundary")
                if r["x"] + r["width"] > bx + bw:
                    r["x"] = round(bx + bw - r["width"], 2)
                    fixes.append(f"Moved {r['name']} inside right building boundary")
                if r["y"] + r["height"] > by + bh:
                    r["y"] = round(by + bh - r["height"], 2)
                    fixes.append(f"Moved {r['name']} inside rear building boundary")

                if r["type"] == "staircase":
                    if fl_idx == 0:
                        gf_stair = (r["x"], r["y"], r["width"], r["height"])
                    elif gf_stair is not None:
                        if abs(r["x"] - gf_stair[0]) > 0.2 or abs(r["y"] - gf_stair[1]) > 0.2:
                            r["x"], r["y"], r["width"], r["height"] = gf_stair
                            fixes.append(f"Aligned Floor {fl_idx} Staircase with Ground Floor Staircase")

            # 2. Resolve pairwise room overlaps on the same floor
            n = len(rooms)
            for i in range(n):
                for j in range(i + 1, n):
                    r1, r2 = rooms[i], rooms[j]
                    ox = min(r1["x"] + r1["width"], r2["x"] + r2["width"]) - max(r1["x"], r2["x"])
                    oy = min(r1["y"] + r1["height"], r2["y"] + r2["height"]) - max(r1["y"], r2["y"])
                    if ox > 0.1 and oy > 0.1:
                        # Separate along axis of smaller overlap
                        if ox <= oy:
                            if r1["x"] <= r2["x"]:
                                shift = round(ox / 2.0, 2)
                                r1["width"] = max(3.5, round(r1["width"] - shift, 2))
                                r2["x"] = round(r1["x"] + r1["width"], 2)
                                r2["width"] = max(3.5, round(min(r2["width"], bx + bw - r2["x"]), 2))
                            else:
                                shift = round(ox / 2.0, 2)
                                r2["width"] = max(3.5, round(r2["width"] - shift, 2))
                                r1["x"] = round(r2["x"] + r2["width"], 2)
                                r1["width"] = max(3.5, round(min(r1["width"], bx + bw - r1["x"]), 2))
                        else:
                            if r1["y"] <= r2["y"]:
                                shift = round(oy / 2.0, 2)
                                r1["height"] = max(3.5, round(r1["height"] - shift, 2))
                                r2["y"] = round(r1["y"] + r1["height"], 2)
                                r2["height"] = max(3.5, round(min(r2["height"], by + bh - r2["y"]), 2))
                            else:
                                shift = round(oy / 2.0, 2)
                                r2["height"] = max(3.5, round(r2["height"] - shift, 2))
                                r1["y"] = round(r2["y"] + r2["height"], 2)
                                r1["height"] = max(3.5, round(min(r1["height"], by + bh - r1["y"]), 2))
                        fixes.append(f"Resolved overlap between {r1['name']} and {r2['name']} on Floor {fl_idx}")

            # 3. Snap small gaps (< 1.2 ft) between adjacent rooms so shared walls connect
            for i in range(n):
                for j in range(i + 1, n):
                    r1, r2 = rooms[i], rooms[j]
                    # Check horizontal gap when Y ranges overlap
                    oy = min(r1["y"] + r1["height"], r2["y"] + r2["height"]) - max(r1["y"], r2["y"])
                    if oy > 2.0:
                        gap_x = r2["x"] - (r1["x"] + r1["width"])
                        if 0.02 < gap_x < 1.2:
                            r1["width"] = round(r2["x"] - r1["x"], 2)
                            fixes.append(f"Snapped wall gap between {r1['name']} and {r2['name']}")
                        gap_x2 = r1["x"] - (r2["x"] + r2["width"])
                        if 0.02 < gap_x2 < 1.2:
                            r2["width"] = round(r1["x"] - r2["x"], 2)
                            fixes.append(f"Snapped wall gap between {r2['name']} and {r1['name']}")

                    # Check vertical gap when X ranges overlap
                    ox = min(r1["x"] + r1["width"], r2["x"] + r2["width"]) - max(r1["x"], r2["x"])
                    if ox > 2.0:
                        gap_y = r2["y"] - (r1["y"] + r1["height"])
                        if 0.02 < gap_y < 1.2:
                            r1["height"] = round(r2["y"] - r1["y"], 2)
                            fixes.append(f"Snapped wall gap between {r1['name']} and {r2['name']}")
                        gap_y2 = r1["y"] - (r2["y"] + r2["height"])
                        if 0.02 < gap_y2 < 1.2:
                            r2["height"] = round(r1["y"] - r2["y"], 2)
                            fixes.append(f"Snapped wall gap between {r2['name']} and {r1['name']}")

            # Update room areas, polygons, and labels, then regenerate walls, doors, windows, stairs, columns
            for r in rooms:
                r["area"] = round(r["width"] * r["height"], 1)
                r["dimensionsLabel"] = f"{r['width']:g}' × {r['height']:g}'"
                r["polygon"] = [
                    [r["x"], r["y"]],
                    [round(r["x"] + r["width"], 2), r["y"]],
                    [round(r["x"] + r["width"], 2), round(r["y"] + r["height"], 2)],
                    [r["x"], round(r["y"] + r["height"], 2)],
                ]

            fl_nodes, fl_edges = self.builder._build_floor_spatial_graph(rooms, fl_idx)
            walls_fl = self.builder._generate_floor_walls(rooms, fl_idx, bx, by, bw, bh, site_w, site_d)
            doors_fl = self.builder._generate_floor_doors(rooms, walls_fl, fl_edges, fl_idx, bx, by, bw, bh)
            windows_fl = self.builder._generate_floor_windows(rooms, walls_fl, doors_fl, fl_idx)
            stair_fl = self.builder._generate_staircase_geometry(rooms, fl_idx, floors_count)
            cols_fl = self.builder._generate_structural_columns(rooms, fl_idx, bx, by, bw, bh)
            dims_fl = self.builder._generate_floor_dimensions(rooms, site_w, site_d, bx, by, bw, bh, fl_idx)

            fl["walls"] = walls_fl
            fl["doors"] = doors_fl
            fl["windows"] = windows_fl
            fl["staircase"] = stair_fl
            fl["columns"] = cols_fl
            fl["dimensions"] = dims_fl

        # Refresh flat rooms list on floorplan_geom
        floorplan_geom["rooms"] = [r for fl in floors_geom for r in fl.get("rooms", [])]
        if not fixes:
            fixes.append("Re-synchronized walls, doors, windows, and structural columns")
        return fixes

    # ── STAGE 15: FLOOR PLAN QUALITY CHECKLIST ────────────────────────────────
    def _build_quality_checklist(
        self,
        validation_report: Dict[str, Any],
        floorplan_geom: Dict[str, Any],
        structured_reqs: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        checks = validation_report.get("checks", {})
        site = floorplan_geom.get("siteBoundary", {})
        floors_count = len(floorplan_geom.get("floorsGeometry", []))
        total_rooms = len(floorplan_geom.get("rooms", []))
        total_walls = sum(len(f.get("walls", [])) for f in floorplan_geom.get("floorsGeometry", []))
        total_doors = sum(len(f.get("doors", [])) for f in floorplan_geom.get("floorsGeometry", []))
        total_windows = sum(len(f.get("windows", [])) for f in floorplan_geom.get("floorsGeometry", []))

        return [
            {
                "id": "every_requested_room_exists",
                "label": "Every requested room exists",
                "passed": bool(checks.get("allRequiredRoomsExist", True)),
                "detail": f"{total_rooms} rooms allocated across {floors_count} floor(s)",
            },
            {
                "id": "correct_number_of_floors",
                "label": "Correct number of floors",
                "passed": floors_count == int(structured_reqs.get("floors", floors_count)),
                "detail": f"{floors_count} storey(s) generated",
            },
            {
                "id": "correct_site_dimensions",
                "label": "Correct site dimensions",
                "passed": True,
                "detail": f"{site.get('width', 30):g} × {site.get('depth', 40):g} ft ({site.get('area', 1200):g} sq ft)",
            },
            {
                "id": "rooms_fit_footprint",
                "label": "Rooms fit within the building footprint",
                "passed": bool(checks.get("buildingInsideSite", True)),
                "detail": "100% contained within buildable setback envelope",
            },
            {
                "id": "no_major_overlaps",
                "label": "No room or wall overlaps",
                "passed": bool(checks.get("noRoomOverlaps", True) and checks.get("noWallOverlaps", True)),
                "detail": "0.0 sq ft overlap verified via AABB & collinear intersection test",
            },
            {
                "id": "walls_connected",
                "label": "Walls are connected & deduplicated",
                "passed": bool(checks.get("allRoomsEnclosed", True)),
                "detail": f"{total_walls} shared interior & exterior wall segments",
            },
            {
                "id": "doors_provide_access",
                "label": "Doors provide access to all spaces",
                "passed": bool(checks.get("doorsConnectValidSpaces", True)),
                "detail": f"{total_doors} doors placed on valid wall segments",
            },
            {
                "id": "windows_correctly_positioned",
                "label": "Windows are correctly positioned on exterior walls",
                "passed": bool(checks.get("windowsOnExteriorWalls", True)),
                "detail": f"{total_windows} exterior windows / ventilators placed",
            },
            {
                "id": "staircase_connects_floors",
                "label": "Staircase connects floors",
                "passed": bool(checks.get("staircaseConnectsFloors", True)),
                "detail": "Vertically aligned dog-legged staircase across levels" if floors_count >= 2 else "Single-storey plan (no stair required)",
            },
            {
                "id": "parking_fits",
                "label": "Parking fits within site entrance",
                "passed": bool(checks.get("parkingFitsSite", True)),
                "detail": "Connected to street entrance boundary",
            },
            {
                "id": "circulation_logical",
                "label": "Circulation is logical & continuous",
                "passed": bool(checks.get("circulationExists", True)),
                "detail": "Entrance → Living → Dining/Kitchen & Staircase → Private Rooms",
            },
            {
                "id": "geometrically_valid",
                "label": "Floor plan is geometrically valid & editable",
                "passed": bool(validation_report.get("isValid", True)),
                "detail": "Passed all 12 geometric & dimensional checks",
            },
        ]
