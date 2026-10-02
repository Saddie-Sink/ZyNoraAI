"""
ZYNORA-ML — Vastu Shastra Compliance Scoring Engine
=====================================================
Evaluates architectural layouts against traditional Indian Vastu Shastra rules.

Vastu Shastra is an ancient Indian system of architecture that defines:
  - Which directions are auspicious for each room type
  - Spatial relationships between zones (public/private/sacred)
  - Proportional rules for dwelling layouts

WHY THIS IS IN THE ML PIPELINE:
  Vastu compliance is used as the 6th objective in NSGA-II Pareto ranking.
  It makes the ranking genuinely India-relevant and academically interesting.
  Each candidate gets a VastuScore alongside the 5 spatial metrics.

VASTU DIRECTIONAL RULES (simplified for computational scoring):
  North-East  (Eeshanya)  → Pooja Room, Meditation, Water feature
  East        (Indra)     → Bedroom, Living room, Main entrance
  South-East  (Agneya)    → Kitchen, Fire-related activities
  South       (Yama)      → Master Bedroom (heavier zone)
  South-West  (Nairutya)  → Master Bedroom alternatively (weight/stability)
  West        (Varuna)    → Dining room, Study
  North-West  (Vaayu)     → Guest bedroom, Garage, Utility
  North       (Kubera)    → Treasury, wealth — Living room, entrance acceptable
  Centre      (Brahmasthana) → Must remain open (courtyard/atrium preferred)
"""

from typing import Dict, List, Any
from .dataset_loader import VASTU_ORIENTATION_SCORES


class VastuScorer:
    """
    Computes a Vastu Shastra compliance score (0–100) for a given
    floor plan candidate based on:
      1. Plot orientation (how the building faces)
      2. Room placement logic (which room type in which zone)
      3. Typological compliance (open central space, zone separation)
      4. Presence of mandatory Indian rooms (Pooja room)
    """

    def __init__(self):
        # Vastu room zone preferences (ideal direction for each room type)
        self.room_direction_scores = {
            "pooja":    {"North-East": 20, "North": 12, "East": 10, "default": 2},
            "kitchen":  {"South-East": 18, "South": 12, "North-West": 8, "default": 3},
            "living":   {"North": 14, "East": 16, "North-East": 12, "default": 5},
            "dining":   {"West": 14, "North-West": 12, "default": 6},
            "bedroom":  {"South": 12, "South-West": 14, "West": 10, "default": 5},
            "bathroom": {"North-West": 14, "West": 12, "East": 6, "default": 3},
            "study":    {"West": 14, "North": 12, "default": 6},
            "utility":  {"North-West": 12, "South-East": 10, "default": 4},
            "balcony":  {"North": 10, "East": 12, "default": 5},
        }

        # Typology-level Vastu compliance
        # Central atrium = open Brahmasthana → excellent Vastu
        # Compact grid = blocked centre → poor Vastu
        self.typology_vastu = {
            "balanced":  8,   # Good zone separation + east-west axis
            "atrium":   12,   # Open Brahmasthana (central void) = best Vastu
            "linear":    6,   # Acceptable — clear N-S or E-W axis
            "compact":   2,   # Blocked centre = Vastu issue
            "segmented": 9,   # Clear public/private zone separation = good
        }

    def score(
        self,
        orientation: str,
        typology: str,
        rooms: List[Dict[str, Any]]
    ) -> int:
        """
        Main scoring method.
        Returns integer Vastu score in range [55, 99].

        Parameters:
          orientation : Plot/building facing direction (e.g. "North", "East")
          typology    : Layout typology code ("balanced", "atrium", etc.)
          rooms       : List of room dicts with 'type' key

        How the score is composed:
          Base score              = 55 (Vastu neutral)
          + Orientation bonus     = 0–18 (from VASTU_ORIENTATION_SCORES)
          + Typology bonus        = 0–12 (from typology_vastu)
          + Pooja room present    = 0–10 (mandatory in Vastu)
          + Room zone check       = 0–10 (simplified zone analysis)
          Total max possible      = 105 → clamped to 99
        """
        score = 55  # Vastu-neutral baseline

        # 1. Orientation contribution
        orientation_bonus = VASTU_ORIENTATION_SCORES.get(orientation, 8)
        score += orientation_bonus

        # 2. Typology contribution
        score += self.typology_vastu.get(typology, 5)

        # 3. Pooja room presence (Vastu REQUIRES a dedicated prayer space in Indian homes)
        has_pooja = any(r.get("type") == "pooja" for r in rooms)
        if has_pooja:
            score += 10  # Significant Vastu compliance bonus
        else:
            score -= 5   # Penalty — traditional Indian Vastu deems this a deficiency

        # 4. Room zone analysis — checks both functional presence and placed vastu_zone
        room_types_present = {r.get("type", "") for r in rooms}
        expected_types = {"living", "kitchen", "bedroom", "bathroom"}
        missing = expected_types - room_types_present
        score -= len(missing) * 3  # Penalty for missing functional zones

        # 5. Coordinate-based Vastu zone alignment (from GNN / Layout Engine placement)
        ideal_zones = {
            "pooja":   {"NE"},
            "kitchen": {"SE", "NW"},
            "bedroom": {"SW", "NW", "S", "W"},
            "living":  {"NE", "N", "E", "C"},
            "dining":  {"C", "W", "E"},
        }
        zone_hits = 0
        zone_checks = 0
        for r in rooms:
            rtype = r.get("type", "")
            rzone = r.get("vastu_zone")
            if rtype in ideal_zones and rzone:
                zone_checks += 1
                if rzone in ideal_zones[rtype]:
                    zone_hits += 1

        if zone_checks > 0:
            zone_ratio = zone_hits / zone_checks
            score += int(round(zone_ratio * 6))

        return max(55, min(99, int(score)))

    def get_vastu_report(
        self,
        orientation: str,
        typology: str,
        rooms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Returns a detailed Vastu compliance report for display in the UI.
        Called by /api/ml/vastu-analysis endpoint.
        """
        vastu_score = self.score(orientation, typology, rooms)
        orientation_bonus = VASTU_ORIENTATION_SCORES.get(orientation, 8)
        has_pooja = any(r.get("type") == "pooja" for r in rooms)

        # Determine Vastu grade
        if vastu_score >= 88:
            grade, grade_label = "A", "Excellent — Highly Vastu-Compliant"
        elif vastu_score >= 78:
            grade, grade_label = "B", "Good — Vastu-Positive Layout"
        elif vastu_score >= 68:
            grade, grade_label = "C", "Acceptable — Minor Vastu Adjustments Recommended"
        else:
            grade, grade_label = "D", "Below Average — Vastu Corrections Needed"

        recommendations = []
        if not has_pooja:
            recommendations.append(
                "Add a dedicated Pooja room in the North-East corner (Eeshanya direction)."
            )
        if orientation in ["South-West", "South"]:
            recommendations.append(
                "South-West facing plots: ensure main entrance is offset to East or North face."
            )
        if typology == "compact":
            recommendations.append(
                "Compact grid blocks the Brahmasthana (centre). "
                "Consider adding a small central courtyard or skylight."
            )
        if orientation in ["North", "North-East", "East"] and not recommendations:
            recommendations.append(
                "Excellent orientation. Maintain open North-East corner for maximum Vastu benefit."
            )

        return {
            "vastuScore":        vastu_score,
            "vastuGrade":        grade,
            "vastuGradeLabel":   grade_label,
            "orientationBonus":  orientation_bonus,
            "hasPooja":          has_pooja,
            "typology":          typology,
            "recommendations":   recommendations,
            "scoringBasis": (
                "Vastu Shastra directional compliance: orientation, room zone placement, "
                "Brahmasthana (central space), and mandatory room presence."
            ),
        }
