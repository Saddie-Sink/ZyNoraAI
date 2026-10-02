"""
ZYNORA-ML — 3D Extrusion Model
================================
MLP that learns room-level 3D geometry parameters from Structured3D dataset.
Given a room's type, area, and floor number, predicts:
  - wall_height     : internal clear height in feet (e.g. 9.0–14.0 ft)
  - floor_thickness : slab thickness in feet (e.g. 0.5–1.0 ft)
  - ceiling_type    : 0=flat, 1=coved, 2=coffered, 3=vaulted

These parameters drive the Three.js 3D extruded room viewer in Zynora.

ARCHITECTURE:
  Input  : [room_type_onehot(9), area_norm(1), floor_idx_norm(1)] = 11 dims
  Hidden : 64 → 128 → 64
  Output : [wall_height_norm(1), floor_thickness_norm(1), ceiling_type_logits(4)]

TRAINING:
  Dataset: Structured3D (3,500 house designs, 3D junctions + planes)
  Loss   : MSE(wall_height) + MSE(floor_thick) + CrossEntropy(ceiling_type)
  Epochs : 80
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

# Wall height range in feet (maps [0,1] → [min, max])
WALL_HEIGHT_MIN = 8.0    # ft — NBC India minimum habitable room height
WALL_HEIGHT_MAX = 16.0   # ft — luxury double-height
FLOOR_THICK_MIN = 0.4    # ft — thin slab
FLOOR_THICK_MAX = 1.2    # ft — thick podium slab

CEILING_TYPES = ["flat", "coved", "coffered", "vaulted"]
NUM_CEILING_TYPES = 4

# Room types (must match gnn_layout_model.py)
ROOM_TYPES = ["living", "dining", "kitchen", "bedroom",
              "bathroom", "pooja", "balcony", "utility", "study"]
NUM_ROOM_TYPES = len(ROOM_TYPES)
ROOM_TYPE_TO_IDX = {rt: i for i, rt in enumerate(ROOM_TYPES)}

# Typical Indian residential wall heights per room type (for warm-starting)
# Used as prior / reference during training
TYPICAL_WALL_HEIGHTS = {
    "living":   12.0,  # Double-height drawing room
    "dining":   10.0,
    "kitchen":   9.5,
    "bedroom":  10.0,
    "bathroom":  9.0,
    "pooja":    10.0,  # High ceiling for sanctity
    "balcony":   9.0,
    "utility":   9.0,
    "study":     9.5,
}


def normalize_wall_height(h_ft: float) -> float:
    return (h_ft - WALL_HEIGHT_MIN) / (WALL_HEIGHT_MAX - WALL_HEIGHT_MIN)


def denormalize_wall_height(h_norm: float) -> float:
    return WALL_HEIGHT_MIN + h_norm * (WALL_HEIGHT_MAX - WALL_HEIGHT_MIN)


def normalize_floor_thick(t_ft: float) -> float:
    return (t_ft - FLOOR_THICK_MIN) / (FLOOR_THICK_MAX - FLOOR_THICK_MIN)


def denormalize_floor_thick(t_norm: float) -> float:
    return FLOOR_THICK_MIN + t_norm * (FLOOR_THICK_MAX - FLOOR_THICK_MIN)


def build_extrusion_input(room_type: str, area_sqft: float,
                          floor_idx: int, max_area: float = 600.0,
                          max_floors: int = 5) -> torch.Tensor:
    """
    Build input feature vector for a single room.
    Returns tensor of shape (11,).
    """
    # Room type one-hot
    onehot = torch.zeros(NUM_ROOM_TYPES)
    onehot[ROOM_TYPE_TO_IDX.get(room_type, 0)] = 1.0

    area_norm  = torch.tensor([min(1.0, area_sqft / max_area)])
    floor_norm = torch.tensor([min(1.0, floor_idx / max_floors)])

    return torch.cat([onehot, area_norm, floor_norm])  # (11,)


class ExtrusionModel(nn.Module):
    """
    MLP that predicts 3D extrusion parameters per room.

    Input  : (B, 11) — [room_type_onehot, area_norm, floor_norm]
    Output : {
        wall_height_norm  : (B, 1) → sigmoid → denormalize to feet
        floor_thick_norm  : (B, 1) → sigmoid → denormalize to feet
        ceiling_logits    : (B, 4) → argmax → ceiling type index
    }
    """

    def __init__(self, input_dim: int = 11, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()

        self.shared_trunk = nn.Sequential(
            nn.Linear(input_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )  # → (B, 64)

        # Wall height head
        self.wall_height_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),  # outputs in (0, 1) → denormalize later
        )

        # Floor thickness head
        self.floor_thick_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

        # Ceiling type head (classification)
        self.ceiling_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, NUM_CEILING_TYPES),  # logits — apply softmax for prob
        )

    def forward(self, x: torch.Tensor) -> dict:
        """
        x : (B, 11)
        Returns dict with wall_height_norm, floor_thick_norm, ceiling_logits
        """
        h = self.shared_trunk(x)                        # (B, 64)
        return {
            "wall_height_norm":  self.wall_height_head(h),    # (B, 1)
            "floor_thick_norm":  self.floor_thick_head(h),    # (B, 1)
            "ceiling_logits":    self.ceiling_head(h),         # (B, 4)
        }


def extrusion_loss(pred: dict, target: dict) -> tuple:
    """
    Combined loss for extrusion model.
    target keys: wall_height_norm (B,1), floor_thick_norm (B,1), ceiling_type (B,) long
    """
    l_height  = F.mse_loss(pred["wall_height_norm"],  target["wall_height_norm"])
    l_thick   = F.mse_loss(pred["floor_thick_norm"],  target["floor_thick_norm"])
    l_ceiling = F.cross_entropy(pred["ceiling_logits"], target["ceiling_type"])

    total = l_height + l_thick + 0.5 * l_ceiling
    return total, {
        "height": l_height.item(),
        "thick":  l_thick.item(),
        "ceiling": l_ceiling.item(),
    }


def predict_extrusion(
    model: ExtrusionModel,
    room_type: str,
    area_sqft: float,
    floor_idx: int = 0,
    device: str = "cpu",
) -> dict:
    """
    Run inference for a single room. Returns 3D parameters in real units.
    """
    model.eval()
    x = build_extrusion_input(room_type, area_sqft, floor_idx).unsqueeze(0).to(device)

    with torch.no_grad():
        out = model(x)

    wall_h = denormalize_wall_height(out["wall_height_norm"].item())
    floor_t = denormalize_floor_thick(out["floor_thick_norm"].item())
    ceiling_idx = out["ceiling_logits"].argmax(dim=-1).item()

    return {
        "wall_height_ft":   round(wall_h, 2),
        "floor_thick_ft":  round(floor_t, 2),
        "ceiling_type":    CEILING_TYPES[ceiling_idx],
        "ceiling_type_idx": ceiling_idx,
    }


def predict_all_rooms_extrusion(
    model: ExtrusionModel,
    rooms: list,
    floor_idx: int = 0,
    device: str = "cpu",
) -> list:
    """
    Run batch inference for all rooms. Returns rooms with added 3D params.
    """
    import copy
    model.eval()
    rooms = copy.deepcopy(rooms)

    inputs = torch.stack([
        build_extrusion_input(r.get("type", "living"), r.get("area", 150), floor_idx)
        for r in rooms
    ]).to(device)  # (N, 11)

    with torch.no_grad():
        out = model(inputs)

    wall_hs = out["wall_height_norm"].cpu().numpy()
    floor_ts = out["floor_thick_norm"].cpu().numpy()
    ceiling_idxs = out["ceiling_logits"].argmax(dim=-1).cpu().numpy()

    for i, room in enumerate(rooms):
        room["wall_height_ft"]  = round(denormalize_wall_height(float(wall_hs[i, 0])), 2)
        room["floor_thick_ft"] = round(denormalize_floor_thick(float(floor_ts[i, 0])), 2)
        room["ceiling_type"]   = CEILING_TYPES[int(ceiling_idxs[i])]

    return rooms
