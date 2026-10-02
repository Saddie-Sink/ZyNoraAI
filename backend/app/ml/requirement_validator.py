"""
ZYNORA-ML — Stage 3: Pre-Generation Requirement Validation
===========================================================
Checks whether the extracted architectural requirements are logically and
geometrically possible on the given site BEFORE generating the 2D floor plan.

Validates:
  • Site dimensions (minimum width & depth)
  • Number of rooms vs available buildable area
  • Number of floors
  • Approximate required area (minimum NBC room areas + circulation)
  • Parking requirements (ground-floor bay dimensions)
  • Staircase requirements (multi-storey vertical connectivity)
  • Minimum circulation requirements (corridors, foyer, wall thickness)
  • Room-size constraints

If the requested requirements cannot reasonably fit within the given site,
explicitly identifies the conflict and provides actionable recommendations.
"""

from typing import Dict, Any, List


# Practical minimum room areas (sq ft) based on NBC India 2016 residential standards
MIN_ROOM_AREAS_SQFT: Dict[str, float] = {
    "living":     130.0,   # ~11 x 12 ft
    "dining":     90.0,    # ~9 x 10 ft
    "kitchen":    65.0,    # ~7.5 x 8.5 ft
    "bedrooms":   110.0,   # ~10 x 11 ft (Master ~130, secondary ~100)
    "bathrooms":  32.0,    # ~5 x 6.5 ft
    "study":      70.0,    # ~8 x 9 ft
    "guest_room": 100.0,   # ~10 x 10 ft
    "utility":    36.0,    # ~6 x 6 ft
    "store_room": 30.0,    # ~5 x 6 ft
    "pooja":      25.0,    # ~5 x 5 ft
    "parking":    135.0,   # ~9 x 15 ft compact / 9 x 16 ft standard bay
    "staircase":  60.0,    # ~6 x 10 ft per floor
    "balcony":    40.0,    # ~4 x 10 ft
    "terrace":    100.0,   # ~10 x 10 ft open slab
    "garden":     60.0,    # front/rear setback strip
}

COMFORTABLE_ROOM_AREAS_SQFT: Dict[str, float] = {
    "living":     190.0,
    "dining":     125.0,
    "kitchen":    95.0,
    "bedrooms":   145.0,
    "bathrooms":  42.0,
    "study":      95.0,
    "guest_room": 125.0,
    "utility":    48.0,
    "store_room": 40.0,
    "pooja":      32.0,
    "parking":    150.0,
    "staircase":  72.0,
    "balcony":    60.0,
    "terrace":    150.0,
    "garden":     90.0,
}


class RequirementValidator:
    """
    Stage 3 of the Architectural Floor Plan Pipeline:
    Validates structured requirements against site geometry and building codes.
    """

    def validate(self, structured_reqs: Dict[str, Any]) -> Dict[str, Any]:
        site = structured_reqs.get("site", {})
        site_w = float(site.get("width", 30.0))
        site_d = float(site.get("depth", 40.0))
        floors = int(structured_reqs.get("floors", 2))
        rooms = structured_reqs.get("requiredRooms", {})
        size_prefs = structured_reqs.get("roomSizePreferences", {})

        conflicts: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []
        recommendations: List[str] = []

        # ── 1. Validate Site Dimensions ───────────────────────────────────────
        if site_w < 15.0 or site_d < 20.0:
            conflicts.append({
                "type": "SITE_DIMENSIONS_TOO_SMALL",
                "severity": "ERROR",
                "message": (
                    f"Site dimensions ({site_w:g} × {site_d:g} ft) are below the minimum "
                    f"habitable residential parcel size (15 × 20 ft)."
                ),
            })
            recommendations.append("Increase site width to at least 20 ft and site depth to at least 30 ft.")

        # Compute realistic setbacks based on plot size
        setback_front = 3.0 if site_d >= 35 else 2.0
        setback_rear  = 2.0 if site_d >= 35 else 1.5
        setback_left  = 2.0 if site_w >= 28 else 1.5
        setback_right = 2.0 if site_w >= 28 else 1.5

        buildable_w = max(10.0, round(site_w - setback_left - setback_right, 2))
        buildable_d = max(12.0, round(site_d - setback_front - setback_rear, 2))
        site_area = round(site_w * site_d, 1)
        footprint_area = round(buildable_w * buildable_d, 1)
        total_buildable_area = round(footprint_area * floors, 1)

        # ── 2. Validate Staircase vs Floors ───────────────────────────────────
        stair_cnt = int(rooms.get("staircase", 0))
        if floors >= 2 and stair_cnt < 1:
            warnings.append({
                "type": "MISSING_STAIRCASE_FOR_MULTI_STOREY",
                "severity": "WARNING",
                "message": f"A {floors}-storey building requires a vertical staircase. Automatically added 1 staircase.",
            })
            rooms["staircase"] = 1
            stair_cnt = 1

        # ── 3. Validate Parking Requirements ──────────────────────────────────
        parking_cnt = int(rooms.get("parking", 0))
        parking_min_area = parking_cnt * MIN_ROOM_AREAS_SQFT["parking"]
        if parking_cnt > 0:
            if buildable_w < 9.0 or buildable_d < 15.0:
                conflicts.append({
                    "type": "PARKING_GEOMETRY_CONFLICT",
                    "severity": "ERROR",
                    "message": (
                        f"Requested {parking_cnt}-car parking requires at least 9 × 15 ft clear bay, "
                        f"which conflicts with buildable envelope ({buildable_w:g} × {buildable_d:g} ft)."
                    ),
                })
            elif parking_min_area > footprint_area * 0.45:
                conflicts.append({
                    "type": "PARKING_EXCEEDS_GROUND_FLOOR",
                    "severity": "ERROR",
                    "message": (
                        f"{parking_cnt}-car parking ({parking_min_area:.0f} sq ft) consumes over 45% "
                        f"of the ground floor buildable footprint ({footprint_area:.0f} sq ft), leaving "
                        f"insufficient space for Living, Kitchen, and Entrance."
                    ),
                })
                recommendations.append("Reduce parking to 1 car or adopt a stilt-parking + upper residential floor configuration.")

        # ── 4. Validate Required Room Areas & Minimum Circulation ─────────────
        min_habitable_area = 0.0
        comfortable_habitable_area = 0.0
        room_breakdown: List[Dict[str, Any]] = []

        for r_key, count in rooms.items():
            cnt = int(count or 0)
            if cnt <= 0 or r_key == "garden":
                continue

            # Staircase occupies area on every connected floor
            effective_cnt = cnt * floors if r_key == "staircase" else cnt
            base_min = MIN_ROOM_AREAS_SQFT.get(r_key, 60.0)
            base_comf = COMFORTABLE_ROOM_AREAS_SQFT.get(r_key, 90.0)

            # Respect explicit user room-size preferences
            pref_key = "bedroom" if r_key == "bedrooms" else r_key
            if pref_key in size_prefs and "area" in size_prefs[pref_key]:
                base_min = max(base_min, float(size_prefs[pref_key]["area"]) * 0.85)
                base_comf = max(base_comf, float(size_prefs[pref_key]["area"]))

            r_min_total = round(base_min * effective_cnt, 1)
            r_comf_total = round(base_comf * effective_cnt, 1)
            min_habitable_area += r_min_total
            comfortable_habitable_area += r_comf_total

            room_breakdown.append({
                "roomType": r_key,
                "count": cnt,
                "effectiveInstances": effective_cnt,
                "minAreaSqFt": r_min_total,
                "comfortableAreaSqFt": r_comf_total,
            })

        # Minimum circulation & wall thickness allowance (14% of habitable area)
        min_circulation_area = round(min_habitable_area * 0.14, 1)
        total_min_required_area = round(min_habitable_area + min_circulation_area, 1)
        total_comfortable_area = round(comfortable_habitable_area * 1.15, 1)

        # Check if total minimum required area exceeds total buildable area across all floors
        utilization_ratio = round(total_min_required_area / max(1.0, total_buildable_area), 2)

        if total_min_required_area > total_buildable_area * 1.05:
            conflicts.append({
                "type": "INSUFFICIENT_FLOOR_AREA",
                "severity": "ERROR",
                "message": (
                    f"Requested rooms + circulation require at least {total_min_required_area:.0f} sq ft, "
                    f"but a {floors}-storey building on a {site_w:g} × {site_d:g} ft site provides "
                    f"at most {total_buildable_area:.0f} sq ft of buildable area "
                    f"({footprint_area:.0f} sq ft/floor after setbacks)."
                ),
            })
            needed_floors = max(floors + 1, int((total_min_required_area / max(1.0, footprint_area)) + 0.99))
            recommendations.append(
                f"Increase building height to {needed_floors} floors, or enlarge site dimensions, "
                f"or reduce bedroom/service room counts."
            )
        elif total_min_required_area > total_buildable_area * 0.90:
            warnings.append({
                "type": "TIGHT_SPACE_FIT",
                "severity": "WARNING",
                "message": (
                    f"Compact space fit ({int(utilization_ratio * 100)}% of buildable envelope). "
                    f"Rooms will be sized near NBC compact thresholds to fit inside {site_w:g} × {site_d:g} ft."
                ),
            })
            recommendations.append("Using compact shared-wall subdivision to maximize carpet efficiency.")

        # ── 5. Check Single-Floor Overcrowding ────────────────────────────────
        total_rooms_count = sum(
            int(rooms.get(k, 0))
            for k in ("bedrooms", "living", "dining", "kitchen", "study", "guest_room", "parking")
        )
        if floors == 1 and total_rooms_count >= 7 and footprint_area < 1100:
            warnings.append({
                "type": "SINGLE_FLOOR_CONGESTION",
                "severity": "WARNING",
                "message": (
                    f"Placing {total_rooms_count} primary spaces on a single floor of {footprint_area:.0f} sq ft "
                    f"reduces individual room sizes. Consider 2 floors for generous rooms."
                ),
            })

        is_valid = len(conflicts) == 0
        status = "VALID" if (is_valid and not warnings) else ("WARNING" if is_valid else "CONFLICT")

        return {
            "isValid": is_valid,
            "status": status,
            "siteAreaSqFt": site_area,
            "buildableFootprintSqFt": footprint_area,
            "buildableWidthFt": buildable_w,
            "buildableDepthFt": buildable_d,
            "setbacksFt": {
                "front": setback_front,
                "rear": setback_rear,
                "left": setback_left,
                "right": setback_right,
            },
            "floors": floors,
            "totalBuildableAreaSqFt": total_buildable_area,
            "minRequiredAreaSqFt": total_min_required_area,
            "comfortableAreaSqFt": total_comfortable_area,
            "minCirculationAreaSqFt": min_circulation_area,
            "utilizationRatio": utilization_ratio,
            "roomBreakdown": room_breakdown,
            "conflicts": conflicts,
            "warnings": warnings,
            "recommendations": recommendations or [
                f"All requested spaces fit comfortably within the {floors}-storey {site_w:g} × {site_d:g} ft envelope."
            ],
            "checks": {
                "siteDimensionsValid": site_w >= 15.0 and site_d >= 20.0,
                "roomCountFeasible": total_min_required_area <= total_buildable_area * 1.05,
                "floorsValid": 1 <= floors <= 4,
                "parkingFeasible": not any(c["type"].startswith("PARKING") for c in conflicts),
                "staircaseValid": floors == 1 or stair_cnt >= 1,
                "circulationAdequate": min_circulation_area >= min_habitable_area * 0.12,
            },
        }
