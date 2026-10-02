"""
ZYNORA-ML — Pareto Multi-Objective Optimizer (Real NSGA-II)
============================================================
Implements genuine NSGA-II (Non-dominated Sorting Genetic Algorithm II)
for multi-objective ranking of floorplan candidates.

BEFORE (old): Simple weighted sum — not real NSGA-II
AFTER  (new): True non-dominated sorting + crowding distance

WHY NSGA-II INSTEAD OF WEIGHTED SUM?
  Weighted sum requires you to decide weights upfront (subjective).
  NSGA-II finds ALL non-dominated solutions — the Pareto Frontier.
  No single solution dominates all others on every objective simultaneously.
  This is the correct approach when objectives conflict (e.g., efficiency
  vs. spaciousness — more efficient layouts are often smaller).

THE 6 OBJECTIVES (maximise all):
  1. efficiency        — space efficiency (RF predicted, Bengaluru data)
  2. connectivity      — circulation graph depth score (NetworkX)
  3. naturalLight      — daylighting surrogate (orientation + typology)
  4. ventilation       — cross-ventilation (building physics surrogate)
  5. requirementMatch  — user brief satisfaction score
  6. vastuScore        — Vastu Shastra compliance (India-specific, NEW)

PARETO DOMINANCE DEFINITION:
  Candidate A dominates Candidate B (A ≻ B) if:
    - A is at least as good as B on ALL 6 objectives, AND
    - A is strictly better than B on at least ONE objective

NON-DOMINATED SORTING:
  Front 1: No candidate dominates them → BEST candidates
  Front 2: Only Front 1 candidates dominate them
  Front 3: Only Front 1 & 2 candidates dominate them
  ...

CROWDING DISTANCE:
  Within the same Pareto front, candidates with larger crowding distance
  are preferred (they are more "isolated" = more diverse solutions).
  This preserves diversity in the solution space.
"""

from typing import List, Dict, Any

# 6 objectives for NSGA-II (all are "maximise")
OBJECTIVES = [
    "efficiency",
    "connectivity",
    "naturalLight",
    "ventilation",
    "requirementMatch",
    "vastuScore",       # 6th objective — India-specific Vastu compliance
]


class ParetoRanker:
    """
    Real NSGA-II implementation for multi-objective floorplan ranking.
    Pure Python — no external optimisation library needed.
    """

    def _dominates(self, a: Dict, b: Dict) -> bool:
        """
        Returns True if candidate 'a' Pareto-dominates candidate 'b'.

        MANUAL UNDERSTANDING:
          For 'a' to dominate 'b':
            1. 'a' must be >= 'b' on EVERY objective (never worse)
            2. 'a' must be > 'b' on AT LEAST ONE objective (strictly better somewhere)

        Example with 3 objectives:
          a = [92, 88, 95]  b = [90, 88, 94]
          a >= b on all:  92>=90 ✓, 88>=88 ✓, 95>=94 ✓
          a > b on some:  92>90 ✓
          → a dominates b ✓
        """
        at_least_one_better = False
        for obj in OBJECTIVES:
            val_a = a.get(obj, 0)
            val_b = b.get(obj, 0)
            if val_a < val_b:
                return False           # 'a' is worse on this objective → cannot dominate
            if val_a > val_b:
                at_least_one_better = True
        return at_least_one_better

    def _non_dominated_sort(
        self,
        candidates: List[Dict]
    ) -> List[List[int]]:
        """
        Assigns each candidate to a Pareto front number.
        Returns list of fronts, where each front is a list of candidate indices.

        MANUAL UNDERSTANDING — the algorithm:
          Step 1: For every pair (i, j), check if i dominates j or j dominates i
          Step 2: Count how many candidates dominate each candidate (domination_count)
          Step 3: Front 1 = all candidates with domination_count = 0 (nobody beats them)
          Step 4: Remove Front 1 candidates, reduce domination counts, repeat for Front 2
          Step 5: Continue until all candidates are assigned to a front
        """
        n = len(candidates)
        domination_count = [0] * n    # How many candidates dominate candidate i?
        dominated_set = [[] for _ in range(n)]  # Which candidates does i dominate?

        # Step 1: Build domination relationships
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if self._dominates(candidates[i], candidates[j]):
                    dominated_set[i].append(j)      # i dominates j
                elif self._dominates(candidates[j], candidates[i]):
                    domination_count[i] += 1         # j dominates i

        # Step 2: Find Front 1 (non-dominated candidates)
        fronts = [[]]
        for i in range(n):
            if domination_count[i] == 0:
                fronts[0].append(i)

        # Step 3: Build subsequent fronts
        k = 0
        while fronts[k]:
            next_front = []
            for i in fronts[k]:
                for j in dominated_set[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            k += 1
            fronts.append(next_front)

        return [f for f in fronts if f]   # Remove empty final list

    def _crowding_distance(
        self,
        front_indices: List[int],
        candidates: List[Dict]
    ) -> Dict[int, float]:
        """
        Computes crowding distance for candidates within the same Pareto front.

        MANUAL UNDERSTANDING:
          For each objective, sort the front by that objective.
          The boundary candidates (min and max) get infinite distance.
          Interior candidates get: (next - prev) / (max - min) normalized distance.
          Sum across all objectives → total crowding distance.

          Higher crowding distance = more isolated = more diverse = PREFERRED
          when two candidates are in the same Pareto front.
        """
        distances = {i: 0.0 for i in front_indices}

        if len(front_indices) <= 2:
            # Boundary points always preferred
            for i in front_indices:
                distances[i] = float("inf")
            return distances

        for obj in OBJECTIVES:
            # Sort front indices by this objective value
            sorted_idx = sorted(
                front_indices,
                key=lambda i: candidates[i].get(obj, 0)
            )
            obj_min = candidates[sorted_idx[0]].get(obj, 0)
            obj_max = candidates[sorted_idx[-1]].get(obj, 0)
            obj_range = max(obj_max - obj_min, 1e-9)

            # Boundary points → infinite distance
            distances[sorted_idx[0]]  = float("inf")
            distances[sorted_idx[-1]] = float("inf")

            # Interior points
            for k in range(1, len(sorted_idx) - 1):
                prev_val = candidates[sorted_idx[k - 1]].get(obj, 0)
                next_val = candidates[sorted_idx[k + 1]].get(obj, 0)
                distances[sorted_idx[k]] += (next_val - prev_val) / obj_range

        return distances

    def _compute_dynamic_weights(
        self,
        project_payload: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Computes dynamic objective weights tailored to the user's specific
        requirements (budget priority, family elderly count, Vastu, ventilation,
        daylighting, plot geometry).
        """
        weights = {
            "requirementMatch": 0.28,
            "efficiency":       0.18,
            "vastuScore":       0.16,
            "connectivity":     0.14,
            "naturalLight":     0.12,
            "ventilation":      0.12,
        }
        if not project_payload or not isinstance(project_payload, dict):
            return weights

        prop = project_payload.get("property", {}) or {}
        fam  = project_payload.get("family", {}) or {}
        bgt  = project_payload.get("budget", {}) or {}
        sty  = project_payload.get("style", {}) or {}

        reqs_raw = fam.get("requirements", []) or []
        reqs_text = " ".join(str(r).lower() for r in reqs_raw)
        custom_text = str(sty.get("customRequirements", "") or "").lower()
        all_prefs = f"{reqs_text} {custom_text}"

        plot_shape = str(prop.get("plotShape", "Rectangle") or "Rectangle").lower()
        if "l-shape" in plot_shape or "l_shape" in plot_shape or "other" in plot_shape:
            weights["requirementMatch"] += 0.12
            weights["connectivity"] += 0.06

        budget_priority = str(bgt.get("priority", "Balanced") or "Balanced").lower()
        if budget_priority == "economy":
            weights["efficiency"] += 0.14
            weights["requirementMatch"] += 0.06
        elif budget_priority == "premium":
            weights["vastuScore"] += 0.04
            weights["naturalLight"] += 0.04
            weights["ventilation"] += 0.04

        if "vastu" in all_prefs or "pooja" in all_prefs or "eeshanya" in all_prefs:
            weights["vastuScore"] += 0.08

        if "ventilation" in all_prefs or "breeze" in all_prefs:
            weights["ventilation"] += 0.07

        if "daylight" in all_prefs or "light" in all_prefs:
            weights["naturalLight"] += 0.07

        elderly = int(fam.get("elderly", 0) or 0)
        if elderly > 0 or "elder" in all_prefs or "accessib" in all_prefs:
            weights["connectivity"] += 0.10
            weights["requirementMatch"] += 0.10

        total_w = sum(weights.values())
        return {k: round(v / total_w, 4) for k, v in weights.items()}

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        project_payload: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Main ranking method. Applies NSGA-II non-dominated sorting combined with
        Requirement-Weighted TOPSIS/Composite tie-breaking within each Pareto front
        to select the #1 Best Floorplan for the user's exact requirements.
        """
        if not candidates:
            return []

        # Step 1: Non-dominated sorting
        fronts = self._non_dominated_sort(candidates)

        # Step 2: Crowding distance within each front
        all_distances: Dict[int, float] = {}
        for front in fronts:
            distances = self._crowding_distance(front, candidates)
            all_distances.update(distances)

        # Step 3: Assign front numbers and dynamic requirement-conditioned composite scores
        idx_to_front: Dict[int, int] = {}
        for front_num, front in enumerate(fronts, start=1):
            for idx in front:
                idx_to_front[idx] = front_num

        weights = self._compute_dynamic_weights(project_payload)
        composites: Dict[int, float] = {}
        for idx, c in enumerate(candidates):
            comp = sum(
                float(c.get(obj, 85)) * weights.get(obj, 0.16)
                for obj in OBJECTIVES
            )
            composites[idx] = round(comp, 2)

        # Step 4: Sort candidates:
        #   Primary:   Pareto front ASC (Front 1 non-dominated always first)
        #   Secondary: Requirement-weighted composite score DESC (crowns the true #1 best match in Front 1)
        #   Tertiary:  Crowding distance DESC
        sorted_indices = sorted(
            range(len(candidates)),
            key=lambda i: (
                idx_to_front.get(i, 99),
                -composites.get(i, 0.0),
                -all_distances.get(i, 0.0)
            )
        )

        # Step 5: Build result list
        result = []
        for rank, idx in enumerate(sorted_indices, start=1):
            c = candidates[idx]
            front_num = idx_to_front.get(idx, len(fronts))
            composite = composites[idx]
            cd = all_distances.get(idx, 0.0)

            rank_label = (
                "#1 Best Floorplan" if rank == 1
                else "#2 Runner-Up" if rank == 2
                else f"#{rank} Alternative"
            )

            result.append({
                "candidateId":      c.get("id", f"cand-{idx}"),
                "code":             c.get("code", f"Candidate {rank}"),
                "title":            c.get("title", ""),
                "rank":             rank,
                "rankLabel":        rank_label,
                "paretoFront":      front_num,
                "isTopRank":        (rank == 1),
                "isBestFloorplan":  (rank == 1),
                "crowdingDistance": round(cd, 4) if cd != float("inf") else 9999.0,
                "compositeScore":   round(composite, 1),
                "qualityScore":     int(round(composite)),
                "matchPercentage":  int(c.get("requirementMatch", 85)),
                "vastuScore":       int(c.get("vastuScore", 75)),
                "efficiency":       int(c.get("efficiency", 85)),
                "naturalLight":     int(c.get("naturalLight", 85)),
                "objectiveWeights": weights,
                # Objectives used in ranking
                "objectives": {
                    obj: c.get(obj, 0) for obj in OBJECTIVES
                },
            })

        return result

