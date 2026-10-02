"""
ZYNORA-ML — Structured3D Dataset Loader
========================================
Loads Structured3D annotations for training the 3D Extrusion Model.
Structured3D: 3,500 house designs with ground-truth 3D structural annotations.

Download: https://structured3d-dataset.org
Format  : ZIP archives per house, each containing:
  Structured3D/
    scene_00000/
      annotation_3d.json  <- junctions, lines, planes, semantics
      ...

We extract per-room:
  - room_type      (from semantic labels)
  - floor_area_m2  (from plane polygon area)
  - wall_height_m  (from junction Z coordinates)
  - ceiling_type   (from plane normal / shape)
"""

import os
import json
import math
import random
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.utils.data import Dataset

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from training.models.extrusion_model import (
    normalize_wall_height, normalize_floor_thick,
    build_extrusion_input, ROOM_TYPE_TO_IDX, CEILING_TYPES,
    WALL_HEIGHT_MIN, WALL_HEIGHT_MAX,
)


# Structured3D semantic label -> our room type
SEMANTIC_MAP = {
    "living room": "living", "lounge": "living",
    "dining room": "dining", "dining": "dining",
    "kitchen": "kitchen",
    "bedroom": "bedroom", "master bedroom": "bedroom",
    "bathroom": "bathroom", "toilet": "bathroom", "wc": "bathroom",
    "balcony": "balcony", "terrace": "balcony",
    "storage": "utility", "utility": "utility", "laundry": "utility",
    "study": "study", "office": "study",
    "prayer room": "pooja", "pooja": "pooja",
}


def map_semantic(label: str) -> str:
    return SEMANTIC_MAP.get(label.lower().strip(), "living")


def junctions_to_height(junctions: list) -> float:
    """Extract wall height in meters from junction Z coordinates."""
    if not junctions:
        return 2.8  # default 2.8m
    zs = [j.get("coordinate", [0, 0, 0])[2] for j in junctions]
    if not zs:
        return 2.8
    h = max(zs) - min(zs)
    return max(2.0, min(5.0, h))  # clamp to realistic range


def plane_to_area_m2(plane_junctions: list) -> float:
    """Shoelace formula on XY plane for floor area."""
    if len(plane_junctions) < 3:
        return 10.0
    pts = np.array([[j[0], j[1]] for j in plane_junctions])
    x, y = pts[:, 0], pts[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    return max(1.0, area)


def classify_ceiling(plane_normal: list) -> int:
    """Classify ceiling type from plane normal vector."""
    if not plane_normal or len(plane_normal) < 3:
        return 0  # flat
    nx, ny, nz = plane_normal
    angle = math.degrees(math.acos(min(1.0, abs(nz) / (math.sqrt(nx**2 + ny**2 + nz**2) + 1e-8))))
    if angle < 5:
        return 0  # flat
    elif angle < 20:
        return 1  # coved
    elif angle < 40:
        return 2  # coffered
    else:
        return 3  # vaulted


class Structured3DDataset(Dataset):
    """
    Dataset for training the ExtrusionModel.
    Each sample = one room with its 3D measurements.

    data_dir should contain scene subdirectories:
      data_dir/scene_00000/annotation_3d.json
      data_dir/scene_00001/annotation_3d.json
      ...
    """

    def __init__(self, data_dir: str, split: str = "train",
                 train_ratio: float = 0.85):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.split    = split
        self.samples  = []

        scene_dirs = sorted(self.data_dir.glob("scene_*"))

        if not scene_dirs:
            print(f"[Structured3DDataset] No scene dirs in {self.data_dir} — using synthetic data")
            self._build_synthetic(1000 if split == "train" else 200)
            return

        n_train = int(len(scene_dirs) * train_ratio)
        scenes = scene_dirs[:n_train] if split == "train" else scene_dirs[n_train:]

        for scene_dir in scenes:
            anno_path = scene_dir / "annotation_3d.json"
            if not anno_path.exists():
                continue
            try:
                self._parse_scene(anno_path)
            except Exception:
                continue

        if not self.samples:
            print(f"[Structured3DDataset] No valid samples parsed — using synthetic")
            self._build_synthetic(800 if split == "train" else 150)

        print(f"[Structured3DDataset] {split}: {len(self.samples)} room samples")

    def _parse_scene(self, anno_path: Path):
        with open(anno_path, encoding="utf-8") as f:
            anno = json.load(f)

        junctions = anno.get("junctions", [])
        semantics  = anno.get("semantics", [])
        planes     = anno.get("planes", [])
        lines      = anno.get("lines",  [])

        # Build junction lookup
        j_coords = {j["ID"]: j.get("coordinate", [0,0,0]) for j in junctions}

        for semantic in semantics:
            label    = semantic.get("type", "living room")
            room_type = map_semantic(label)
            plane_ids = semantic.get("planeID", [])

            if not plane_ids:
                continue

            # Get floor plane (horizontal plane facing up)
            floor_area = 10.0
            ceiling_type = 0
            for pid in plane_ids:
                if pid >= len(planes):
                    continue
                plane = planes[pid]
                normal = plane.get("normal", [0,0,1])
                if abs(normal[2]) > 0.8:  # mostly horizontal
                    j_ids = plane.get("junctionID", [])
                    pts = [j_coords[jid] for jid in j_ids if jid in j_coords]
                    if pts:
                        area = plane_to_area_m2([p[:2] for p in pts])
                        if area > floor_area:
                            floor_area = area
                    ceiling_type = classify_ceiling(normal)

            # Wall height from junctions
            room_junctions = []
            for pid in plane_ids:
                if pid >= len(planes):
                    continue
                j_ids = planes[pid].get("junctionID", [])
                room_junctions.extend([{"coordinate": j_coords[jid]} for jid in j_ids if jid in j_coords])

            wall_h_m = junctions_to_height(room_junctions)
            wall_h_ft = wall_h_m * 3.281
            floor_thick_ft = random.uniform(0.5, 0.9)  # Structured3D doesn't annotate slab thickness
            area_ft2 = floor_area * 10.764

            self.samples.append({
                "room_type":       room_type,
                "area_sqft":       area_ft2,
                "wall_height_ft":  wall_h_ft,
                "floor_thick_ft":  floor_thick_ft,
                "ceiling_type":    ceiling_type,
                "floor_idx":       0,
            })

    def _build_synthetic(self, n: int):
        """Synthetic samples based on typical Indian room measurements."""
        TYPICAL = {
            "living":   {"h": 12.0, "a": 320}, "dining": {"h": 10.0, "a": 180},
            "kitchen":  {"h": 9.5,  "a": 145}, "bedroom": {"h": 10.0, "a": 190},
            "bathroom": {"h": 9.0,  "a": 65},  "pooja":   {"h": 10.0, "a": 58},
            "balcony":  {"h": 9.0,  "a": 100}, "utility": {"h": 9.0,  "a": 110},
            "study":    {"h": 9.5,  "a": 130},
        }
        room_types = list(TYPICAL.keys())
        for _ in range(n):
            rt = random.choice(room_types)
            base = TYPICAL[rt]
            self.samples.append({
                "room_type":      rt,
                "area_sqft":      base["a"] * random.uniform(0.7, 1.5),
                "wall_height_ft": base["h"] + random.gauss(0, 0.5),
                "floor_thick_ft": random.uniform(0.5, 0.9),
                "ceiling_type":   random.choices([0,1,2,3], weights=[0.6,0.2,0.15,0.05])[0],
                "floor_idx":      random.randint(0, 2),
            })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        x = build_extrusion_input(
            s["room_type"], s["area_sqft"], s["floor_idx"]
        )  # (11,)

        wall_h_norm  = normalize_wall_height(
            max(WALL_HEIGHT_MIN, min(WALL_HEIGHT_MAX, s["wall_height_ft"]))
        )
        floor_t_norm = normalize_floor_thick(
            max(0.4, min(1.2, s["floor_thick_ft"]))
        )

        target = {
            "wall_height_norm":  torch.tensor([wall_h_norm], dtype=torch.float),
            "floor_thick_norm":  torch.tensor([floor_t_norm], dtype=torch.float),
            "ceiling_type":      torch.tensor(s["ceiling_type"], dtype=torch.long),
        }
        return x, target