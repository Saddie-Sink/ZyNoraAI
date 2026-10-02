"""
ZYNORA-ML — Stages 1 & 2: Natural Language Requirement Understanding & Extraction
==================================================================================
Converts natural-language architectural requirements or structured form payloads
into explicit, structured architectural constraints, separating:
  - MANDATORY REQUIREMENTS
  - OPTIONAL / PREFERENCE REQUIREMENTS

Extracts all 23 architectural attributes:
  • Site width, Site depth, Site shape
  • Number of floors
  • Number of bedrooms, Number of bathrooms
  • Living room, Dining room, Kitchen
  • Study room, Guest room, Utility room, Store room, Pooja room
  • Parking (number of cars)
  • Staircase (auto-required if floors >= 2)
  • Balcony, Terrace, Garden / open space
  • Entrance requirements (orientation)
  • Approximate room-size preferences
  • Room priorities, Style preferences, Special user requirements
"""

import re
from typing import Dict, Any, List, Optional, Tuple


WORD_TO_NUM: Dict[str, int] = {
    "zero": 0, "no": 0, "none": 0,
    "a": 1, "an": 1, "one": 1, "single": 1, "simplex": 1,
    "two": 2, "double": 2, "duplex": 2, "couple": 2,
    "three": 3, "triple": 3, "triplex": 3,
    "four": 4, "quad": 4,
    "five": 5,
    "six": 6,
}


def _parse_int_token(token: str, default: int = 1) -> int:
    if not token:
        return default
    t = token.strip().lower()
    if t.isdigit():
        return int(t)
    return WORD_TO_NUM.get(t, default)


class NLPRequirementExtractor:
    """
    Stages 1 & 2 of the Floor Plan Generation Pipeline:
      1. Requirement Understanding
      2. Requirement Extraction (Mandatory vs Optional/Preference)
    """

    def extract(
        self,
        prompt: Optional[str] = None,
        project_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extracts structured architectural requirements from natural-language text,
        merging with structured form data when provided.
        """
        payload = project_payload or {}
        prop = payload.get("property", {}) or {}
        fam = payload.get("family", {}) or {}
        rooms_form = fam.get("rooms", {}) if isinstance(fam.get("rooms"), dict) else {}
        loc = payload.get("location", {}) or {}
        sty = payload.get("style", {}) or {}

        raw_text = (prompt or payload.get("nlPrompt") or sty.get("customRequirements") or "").strip()
        text_lower = raw_text.lower()
        has_nl = len(text_lower) > 5

        mandatory: List[Dict[str, Any]] = []
        optional: List[Dict[str, Any]] = []

        # ── 1. SITE DIMENSIONS & SHAPE ────────────────────────────────────────
        site_width = float(prop.get("siteWidth") or 30.0)
        site_depth = float(prop.get("siteLength") or prop.get("siteDepth") or 40.0)
        site_shape = str(prop.get("plotShape") or "rectangular").lower()
        site_from_nl = False

        if has_nl:
            # Match patterns like "30 × 40 ft", "30x40", "30 by 40 feet", "30' x 40'"
            dim_match = re.search(
                r"(\d+(?:\.\d+)?)\s*(?:ft|feet|foot|')?\s*(?:x|×|\*|by)\s*(\d+(?:\.\d+)?)\s*(?:ft|feet|foot|'|site|plot)?",
                text_lower,
            )
            if dim_match:
                site_width = float(dim_match.group(1))
                site_depth = float(dim_match.group(2))
                site_from_nl = True

            # Match explicit width / depth
            w_match = re.search(r"(?:width|frontage)\s*(?:of|:|=)?\s*(\d+(?:\.\d+)?)\s*(?:ft|feet)?", text_lower)
            d_match = re.search(r"(?:depth|length)\s*(?:of|:|=)?\s*(\d+(?:\.\d+)?)\s*(?:ft|feet)?", text_lower)
            if w_match:
                site_width = float(w_match.group(1))
                site_from_nl = True
            if d_match:
                site_depth = float(d_match.group(1))
                site_from_nl = True

            if "l-shape" in text_lower or "l shape" in text_lower:
                site_shape = "l_shape"
            elif "t-shape" in text_lower or "t shape" in text_lower:
                site_shape = "t_shape"
            elif "courtyard" in text_lower or "atrium" in text_lower:
                site_shape = "courtyard"
            elif "square" in text_lower:
                site_shape = "square"
            elif "rectang" in text_lower or site_from_nl:
                site_shape = "rectangular"

        mandatory.append({
            "category": "site",
            "key": "site_dimensions",
            "label": f"Site Dimensions: {site_width:g} × {site_depth:g} ft ({site_shape})",
            "value": {"width": site_width, "depth": site_depth, "shape": site_shape},
        })

        # ── 2. NUMBER OF FLOORS ───────────────────────────────────────────────
        floors = int(prop.get("floors") or 2)
        if has_nl:
            # Check G+1, G+2
            g_plus = re.search(r"\bg\s*\+\s*(\d+)\b", text_lower)
            if g_plus:
                floors = 1 + int(g_plus.group(1))
            else:
                fl_match = re.search(
                    r"\b(one|two|three|four|single|double|triple|duplex|triplex|\d+)\s*[-\s]*(?:storey|storeys|story|stories|floor|floors|level|levels)\b",
                    text_lower,
                )
                if fl_match:
                    tok = fl_match.group(1)
                    floors = _parse_int_token(tok, floors)
                elif "duplex" in text_lower:
                    floors = 2
                elif "single-storey" in text_lower or "single floor" in text_lower or "bungalow" in text_lower:
                    floors = 1

        floors = max(1, min(4, floors))
        mandatory.append({
            "category": "building",
            "key": "floors",
            "label": f"Floors: {floors} {'Storey' if floors == 1 else 'Storeys'}",
            "value": floors,
        })

        # ── 3. ROOM COUNTS (MANDATORY vs OPTIONAL) ────────────────────────────
        def extract_room_count(
            patterns: List[str],
            form_key: str,
            default_val: int,
            is_core: bool = False,
        ) -> Tuple[int, bool]:
            """Returns (count, explicitly_mentioned_in_nl)."""
            if has_nl:
                for pat in patterns:
                    m = re.search(pat, text_lower)
                    if m:
                        if m.groups():
                            cnt = _parse_int_token(m.group(1), 1)
                        else:
                            cnt = 1
                        return cnt, True
                # If prompt is a full sentence specifying rooms ("I need 3 bedrooms..."),
                # non-mentioned optional rooms should default to 0 unless core (living/kitchen/bath)
                if not is_core:
                    return 0, False
                return (1 if default_val >= 1 else default_val), False
            else:
                val = rooms_form.get(form_key, default_val)
                return int(round(float(val if val is not None else default_val))), False

        # Bedrooms (also support "3 BHK" / "3bhk")
        bedrooms, bed_explicit = extract_room_count(
            [
                r"\b(one|two|three|four|five|six|\d+)\s*[-\s]*(?:bed\s*rooms?|bedrooms?|beds?|bhk)\b",
                r"\b(master\s+bedroom)\b",
            ],
            "bedrooms",
            int(rooms_form.get("bedrooms") or 3),
            is_core=True,
        )
        bedrooms = max(1, min(6, bedrooms))

        # Bathrooms
        bathrooms, bath_explicit = extract_room_count(
            [
                r"\b(one|two|three|four|five|six|\d+)\s*[-\s]*(?:bath\s*rooms?|bathrooms?|baths?|toilets?|restrooms?|washrooms?)\b",
            ],
            "bathrooms",
            int(round(float(rooms_form.get("bathrooms") or bedrooms))),
            is_core=True,
        )
        if has_nl and not bath_explicit:
            bathrooms = max(1, bedrooms)
        bathrooms = max(1, min(6, bathrooms))

        # Living Room
        living, liv_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:living\s*rooms?|living\s*area|drawing\s*rooms?|hall|lounge)\b",
            ],
            "livingRoom",
            1,
            is_core=True,
        )
        living = max(1, min(2, living))

        # Dining Room
        dining, din_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:dining\s*rooms?|dining\s*area|dining\s*hall|dining)\b",
            ],
            "dining",
            1,
            is_core=False,
        )
        if not has_nl and "dining" not in rooms_form:
            dining = 1

        # Kitchen
        kitchen, kit_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:modular\s*kitchen|kitchens?|kitchenette)\b",
            ],
            "kitchen",
            1,
            is_core=True,
        )
        kitchen = max(1, min(2, kitchen))

        # Study Room
        study, study_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:study\s*rooms?|study|home\s*office|office\s*room|work\s*room)\b",
            ],
            "study",
            int(rooms_form.get("study") or 0),
            is_core=False,
        )

        # Guest Room
        guest_room, guest_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:guest\s*rooms?|guest\s*bedroom|guest\s*suite)\b",
            ],
            "guestRoom",
            int(rooms_form.get("guestRoom") or 0),
            is_core=False,
        )

        # Utility Room
        utility, util_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:utility\s*rooms?|utility\s*area|utility|laundry|wash\s*area)\b",
            ],
            "utility",
            int(rooms_form.get("utility") if "utility" in rooms_form else (0 if has_nl else 1)),
            is_core=False,
        )

        # Store Room
        store_room, store_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:store\s*rooms?|storage\s*room|pantry|store)\b",
            ],
            "storeRoom",
            int(rooms_form.get("storeRoom") or 0),
            is_core=False,
        )

        # Pooja Room
        pooja, pooja_explicit = extract_room_count(
            [
                r"\b(one|\d+|a|an)?\s*(?:pooja\s*rooms?|puja\s*room|prayer\s*room|mandir)\b",
            ],
            "pooja",
            int(rooms_form.get("pooja") if "pooja" in rooms_form else (0 if has_nl else 1)),
            is_core=False,
        )

        # Parking
        parking, park_explicit = extract_room_count(
            [
                r"\b(one|two|three|\d+|a|an)?\s*[-\s]*(?:car\s*parkings?|car\s*park|car\s*garage|parkings?|garage|portico)\b",
            ],
            "parking",
            int(rooms_form.get("parking") if "parking" in rooms_form else (0 if has_nl else 1)),
            is_core=False,
        )

        # Balcony
        balcony, bal_explicit = extract_room_count(
            [
                r"\b(one|two|three|\d+|a|an)?\s*(?:balcon(?:y|ies)|verandah|sit[\s-]*out)\b",
            ],
            "balcony",
            int(rooms_form.get("balcony") if "balcony" in rooms_form else 1),
            is_core=False,
        )

        # Terrace
        terrace, ter_explicit = extract_room_count(
            [
                r"\b(one|two|\d+|a|an)?\s*(?:terraces?|roof\s*deck|open\s*terrace)\b",
            ],
            "terrace",
            int(rooms_form.get("terrace") or 0),
            is_core=False,
        )

        # Garden / Open Space
        garden, gar_explicit = extract_room_count(
            [
                r"\b(one|\d+|a|an)?\s*(?:gardens?|lawn|backyard|front\s*yard|courtyard|open\s*space)\b",
            ],
            "garden",
            int(rooms_form.get("garden") or 0),
            is_core=False,
        )

        # Staircase (automatically mandatory if floors >= 2 or explicitly requested)
        stair_explicit = bool(re.search(r"\b(staircase|stairs|stairway|internal\s*stairs)\b", text_lower)) if has_nl else False
        staircase = 1 if (floors >= 2 or stair_explicit) else 0

        # ── 4. ENTRANCE, ORIENTATION & STYLE PREFERENCES ──────────────────────
        entrance_dir = str(loc.get("orientation") or prop.get("orientation") or "East")
        entrance_explicit = False
        if has_nl:
            dir_match = re.search(
                r"\b(north[-\s]*east|north[-\s]*west|south[-\s]*east|south[-\s]*west|north|south|east|west)\s*[-\s]*(?:facing|entrance|entry|oriented|plot|site)?\b",
                text_lower,
            )
            if dir_match:
                raw_dir = dir_match.group(1).replace(" ", "-").title()
                entrance_dir = raw_dir
                entrance_explicit = True

        style_pref = str(sty.get("architecturalStyle") or "Modern")
        style_explicit = False
        if has_nl:
            for s_kw, s_label in [
                ("modern", "Modern Contemporary"),
                ("contemporary", "Contemporary"),
                ("minimalist", "Minimalist"),
                ("traditional", "Traditional Indian"),
                ("chettinad", "Chettinad Vernacular"),
                ("kerala", "Kerala Courtyard"),
                ("colonial", "Indo-Colonial"),
                ("luxury", "Luxury Contemporary Villa"),
                ("biophilic", "Biophilic Courtyard"),
            ]:
                if s_kw in text_lower:
                    style_pref = s_label
                    style_explicit = True
                    break

        # ── 5. ROOM SIZE PREFERENCES & PRIORITIES ─────────────────────────────
        room_size_prefs: Dict[str, Any] = {}
        room_priorities: List[str] = []
        special_requirements: List[str] = list(fam.get("requirements") or [])

        if has_nl:
            # Explicit room dimension preferences like "14x16 master bedroom" or "living room 16x20"
            for rtype, rpat in [
                ("living", r"(?:living(?:\s*room)?|hall)\s*(?:of\s*)?(\d+)\s*[x×*]\s*(\d+)"),
                ("bedroom", r"(?:master\s*bed(?:room)?|bedroom)\s*(?:of\s*)?(\d+)\s*[x×*]\s*(\d+)"),
                ("kitchen", r"kitchen\s*(?:of\s*)?(\d+)\s*[x×*]\s*(\d+)"),
                ("dining", r"dining(?:\s*room)?\s*(?:of\s*)?(\d+)\s*[x×*]\s*(\d+)"),
            ]:
                m = re.search(rpat, text_lower)
                if m:
                    w_p, h_p = float(m.group(1)), float(m.group(2))
                    room_size_prefs[rtype] = {"width": w_p, "height": h_p, "area": round(w_p * h_p)}

            # Qualitative room size modifiers ("spacious living room", "large master bedroom", "compact kitchen")
            for mod_kw, factor in [("spacious", 1.2), ("large", 1.2), ("big", 1.15), ("compact", 0.85), ("small", 0.85)]:
                for r_kw in ["living", "bedroom", "master", "kitchen", "dining", "balcony", "terrace"]:
                    if re.search(rf"\b{mod_kw}\s+(?:[a-z]+\s+)?{r_kw}\b", text_lower):
                        key = "bedroom" if r_kw == "master" else r_kw
                        if key not in room_size_prefs:
                            room_size_prefs[key] = {"scale_factor": factor, "modifier": mod_kw}
                        room_priorities.append(f"{mod_kw.title()} {r_kw.title()}")

            # Special requirements from text
            for kw, label in [
                ("vastu", "Vastu Shastra Compliance"),
                ("cross ventilation", "Cross Ventilation"),
                ("ventilation", "Natural Ventilation"),
                ("natural light", "Maximum Daylighting"),
                ("daylight", "Maximum Daylighting"),
                ("elder", "Elder-Friendly Ground Floor Suite"),
                ("wheelchair", "Accessible Zero-Threshold Circulation"),
                ("open kitchen", "Open-Plan Kitchen & Dining"),
                ("attached bath", "Attached En-Suite Bathrooms"),
                ("courtyard", "Central Open Courtyard"),
                ("double height", "Double-Height Living Volume"),
            ]:
                if kw in text_lower and label not in special_requirements:
                    special_requirements.append(label)

        # ── 6. POPULATE MANDATORY vs OPTIONAL LISTS ───────────────────────────
        required_rooms = {
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "living": living,
            "dining": dining,
            "kitchen": kitchen,
            "study": study,
            "guest_room": guest_room,
            "utility": utility,
            "store_room": store_room,
            "pooja": pooja,
            "parking": parking,
            "staircase": staircase,
            "balcony": balcony,
            "terrace": terrace,
            "garden": garden,
        }

        room_labels = {
            "bedrooms": "Bedrooms",
            "bathrooms": "Bathrooms",
            "living": "Living Room",
            "dining": "Dining Room",
            "kitchen": "Kitchen",
            "study": "Study Room",
            "guest_room": "Guest Room",
            "utility": "Utility Room",
            "store_room": "Store Room",
            "pooja": "Pooja Room",
            "parking": "Car Parking",
            "staircase": "Staircase",
            "balcony": "Balcony",
            "terrace": "Terrace",
            "garden": "Garden / Open Space",
        }

        explicit_map = {
            "bedrooms": True,
            "bathrooms": True,
            "living": True,
            "kitchen": True,
            "dining": din_explicit or dining > 0,
            "study": study_explicit,
            "guest_room": guest_explicit,
            "utility": util_explicit,
            "store_room": store_explicit,
            "pooja": pooja_explicit,
            "parking": park_explicit or parking > 0,
            "staircase": floors >= 2 or stair_explicit,
            "balcony": bal_explicit or balcony > 0,
            "terrace": ter_explicit or terrace > 0,
            "garden": gar_explicit,
        }

        for r_key, r_cnt in required_rooms.items():
            if r_cnt <= 0:
                continue
            item = {
                "category": "room",
                "key": r_key,
                "label": f"{room_labels[r_key]}: {r_cnt}",
                "count": r_cnt,
            }
            if explicit_map.get(r_key, False):
                mandatory.append(item)
            else:
                optional.append(item)

        if style_pref:
            (optional if not style_explicit else optional).append({
                "category": "style",
                "key": "architectural_style",
                "label": f"Style Preference: {style_pref}",
                "value": style_pref,
            })

        if entrance_dir:
            target_list = mandatory if entrance_explicit else optional
            target_list.append({
                "category": "entrance",
                "key": "entrance_direction",
                "label": f"Entrance Orientation: {entrance_dir}-Facing",
                "value": entrance_dir,
            })

        for sp in special_requirements:
            optional.append({
                "category": "preference",
                "key": "special_requirement",
                "label": sp,
                "value": sp,
            })

        # Compute target built-up area based on site footprint and floors
        # Leave practical setback margin (~18-22% of site area for setbacks/open space)
        site_area = round(site_width * site_depth, 1)
        footprint_ratio = 0.78 if site_area <= 1500 else 0.75
        estimated_built_up = round(site_area * footprint_ratio * floors)
        if not site_from_nl and prop.get("builtUpArea"):
            target_built_up = float(prop.get("builtUpArea"))
        else:
            target_built_up = float(estimated_built_up)

        structured = {
            "sourcePrompt": raw_text,
            "parsedFromNL": has_nl,
            "site": {
                "width": site_width,
                "depth": site_depth,
                "area": site_area,
                "shape": site_shape,
                "unit": "ft",
                "entranceDirection": entrance_dir,
            },
            "floors": floors,
            "targetBuiltUpArea": target_built_up,
            "requiredRooms": required_rooms,
            "parking": {
                "required": parking > 0,
                "cars": parking,
            },
            "staircase": {
                "required": staircase > 0,
                "connectsFloors": list(range(floors)),
            },
            "roomSizePreferences": room_size_prefs,
            "roomPriorities": room_priorities,
            "stylePreference": style_pref,
            "specialRequirements": special_requirements,
            "mandatoryRequirements": mandatory,
            "optionalRequirements": optional,
            # Ready-to-merge wizard state for frontend sync
            "wizardSync": {
                "property": {
                    "siteWidth": site_width,
                    "siteLength": site_depth,
                    "floors": floors,
                    "builtUpArea": target_built_up,
                    "plotShape": "L-shape" if site_shape == "l_shape" else "Rectangle",
                    "orientation": entrance_dir,
                },
                "location": {
                    "orientation": entrance_dir,
                },
                "family": {
                    "rooms": {
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "livingRoom": living,
                        "dining": dining,
                        "kitchen": kitchen,
                        "study": study,
                        "guestRoom": guest_room,
                        "utility": utility,
                        "storeRoom": store_room,
                        "pooja": pooja,
                        "parking": parking,
                        "balcony": balcony,
                        "terrace": terrace,
                        "garden": garden,
                    },
                    "requirements": special_requirements,
                },
                "style": {
                    "architecturalStyle": style_pref,
                    "customRequirements": raw_text if has_nl else sty.get("customRequirements", ""),
                },
            },
        }
        return structured
