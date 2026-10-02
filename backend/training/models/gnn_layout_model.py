"""
ZYNORA-ML — GNN Layout Model
==============================
Graph Attention Network (GAT) that learns to place Indian residential rooms
on a plot given user requirements (BHK, sqft, orientation, plot shape).

ARCHITECTURE:
  Input Graph:
    Nodes = rooms (type + area + vastu preference)
    Edges = spatial adjacency (kitchen↔dining, bedroom↔bathroom, etc.)
  
  Model:
    1. Node feature embedding  Linear(12 → 64)
    2. GATConv layer 1         (64 → 64, heads=4, edge_dim=2)
    3. GATConv layer 2         (256 → 64, heads=4)
    4. GATConv layer 3         (256 → 32, heads=1)
    5. Plot context embedding  Linear(15 → 32)
    6. Coordinate head         Linear(64 → 4) → sigmoid → [x,y,w,h]

  Output per node: (x_norm, y_norm, w_norm, h_norm) in [0, 1]
    x_norm * plot_w → actual x in feet
    y_norm * plot_h → actual y in feet
    w_norm * plot_w → actual width in feet
    h_norm * plot_h → actual height in feet

TRAINING:
  Dataset: ResPlan (17K plans) + RPLAN (80K plans)
  Loss: L1(coords) + overlap_penalty + vastu_penalty
  Optimizer: AdamW, lr=1e-3, weight_decay=1e-4
  Epochs: 100 (early stopping patience=10)
  Batch: 32 graphs
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

# PyTorch Geometric imports — installed via: pip install torch-geometric
try:
    from torch_geometric.nn import GATConv, global_mean_pool
    from torch_geometric.data import Data, Batch
    GEO_AVAILABLE = True
except ImportError:
    GEO_AVAILABLE = False
    print("[WARNING] torch_geometric not installed. Run: pip install torch-geometric")


# ─── Room Type Vocabulary ──────────────────────────────────────────────────────
# Must match RPLAN_ROOM_PRIORS keys in dataset_loader.py
ROOM_TYPES = [
    "living", "dining", "kitchen", "bedroom",
    "bathroom", "pooja", "balcony", "utility", "study"
]
NUM_ROOM_TYPES = len(ROOM_TYPES)  # 9
ROOM_TYPE_TO_IDX = {rt: i for i, rt in enumerate(ROOM_TYPES)}

# ─── Plot Shape Vocabulary ────────────────────────────────────────────────────
PLOT_SHAPES = ["rectangular", "l_shape", "t_shape", "courtyard", "stepped"]
NUM_PLOT_SHAPES = len(PLOT_SHAPES)  # 5
SHAPE_TO_IDX = {s: i for i, s in enumerate(PLOT_SHAPES)}

# ─── Orientation Vocabulary ───────────────────────────────────────────────────
ORIENTATIONS = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
NUM_ORIENTATIONS = len(ORIENTATIONS)  # 8
ORIENT_TO_IDX = {o: i for i, o in enumerate(ORIENTATIONS)}

# ─── Vastu Zone → normalized (x, y) preference ───────────────────────────────
VASTU_ZONE_XY = {
    "NE": (0.75, 0.75), "NW": (0.25, 0.75),
    "SE": (0.75, 0.25), "SW": (0.25, 0.25),
    "C":  (0.50, 0.50),
}
VASTU_ROOM_PREFS = {
    "living": "NE", "dining": "C",  "kitchen": "SE", "bedroom": "SW",
    "bathroom": "SW", "pooja": "NE", "balcony": "NE", "utility": "NW", "study": "NW",
}


def room_type_to_onehot(room_type: str) -> torch.Tensor:
    """Returns a one-hot vector of shape (NUM_ROOM_TYPES,) for a room type."""
    idx = ROOM_TYPE_TO_IDX.get(room_type, 0)
    v = torch.zeros(NUM_ROOM_TYPES)
    v[idx] = 1.0
    return v


def build_node_features(rooms: list, plot_area: float) -> torch.Tensor:
    """
    Build node feature matrix X of shape (N_rooms, 12).
    Features per node:
      [0:9]  room_type one-hot  (9 dims)
      [9]    normalized area    (area / plot_area)
      [10]   vastu pref x       (from VASTU_ZONE_XY)
      [11]   vastu pref y
    """
    rows = []
    for room in rooms:
        rtype = room.get("type", "living")
        area_norm = min(1.0, room.get("area", 100) / max(1, plot_area))
        zone = VASTU_ROOM_PREFS.get(rtype, "C")
        px, py = VASTU_ZONE_XY.get(zone, (0.5, 0.5))
        onehot = room_type_to_onehot(rtype)
        feat = torch.cat([onehot, torch.tensor([area_norm, px, py])])
        rows.append(feat)
    return torch.stack(rows)  # (N, 12)


def build_edge_index(rooms: list) -> tuple:
    """
    Builds adjacency edges based on functional Indian residential rules:
      kitchen ↔ dining, living ↔ dining, living ↔ balcony,
      bedroom ↔ bathroom (each pair), pooja ↔ living
    Returns edge_index (2, E) and edge_attr (E, 2).
    """
    n = len(rooms)
    type_to_indices = {}
    for i, room in enumerate(rooms):
        rt = room.get("type", "living")
        type_to_indices.setdefault(rt, []).append(i)

    ADJACENCY_RULES = [
        ("kitchen",  "dining",   [1, 1]),
        ("living",   "dining",   [1, 0]),
        ("living",   "balcony",  [1, 0]),
        ("living",   "pooja",    [0, 1]),
        ("bedroom",  "bathroom", [1, 1]),
        ("dining",   "utility",  [0, 1]),
    ]

    edges, attrs = [], []
    for src_type, dst_type, attr in ADJACENCY_RULES:
        for si in type_to_indices.get(src_type, []):
            for di in type_to_indices.get(dst_type, []):
                if si != di:
                    edges.append([si, di])
                    edges.append([di, si])
                    attrs.append(attr)
                    attrs.append(attr)

    if not edges:
        # Fully connected fallback (chain)
        for i in range(n - 1):
            edges.extend([[i, i+1], [i+1, i]])
            attrs.extend([[0, 0], [0, 0]])

    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()  # (2, E)
    edge_attr  = torch.tensor(attrs, dtype=torch.float)                   # (E, 2)
    return edge_index, edge_attr


def build_plot_context(plot_shape: str, plot_w: float, plot_h: float,
                       orientation: str, max_dim: float = 100.0) -> torch.Tensor:
    """
    Build plot-level context vector of shape (15,):
      [0:5]  plot_shape one-hot
      [5]    plot_w / max_dim
      [6]    plot_h / max_dim
      [7:15] orientation one-hot
    """
    shape_oh = torch.zeros(NUM_PLOT_SHAPES)
    shape_oh[SHAPE_TO_IDX.get(plot_shape, 0)] = 1.0

    dims = torch.tensor([plot_w / max_dim, plot_h / max_dim])

    orient_oh = torch.zeros(NUM_ORIENTATIONS)
    orient_oh[ORIENT_TO_IDX.get(orientation, 2)] = 1.0  # default East

    return torch.cat([shape_oh, dims, orient_oh])  # (15,)


def rooms_to_graph(rooms: list, plot_shape: str, plot_w: float, plot_h: float,
                   orientation: str, target_coords=None) -> "Data":
    """
    Converts a list of room dicts → torch_geometric Data object.
    If target_coords is provided (list of [x,y,w,h] normalized), adds y label.
    """
    if not GEO_AVAILABLE:
        raise RuntimeError("torch_geometric not installed")

    plot_area = plot_w * plot_h
    x         = build_node_features(rooms, plot_area)
    edge_index, edge_attr = build_edge_index(rooms)
    context   = build_plot_context(plot_shape, plot_w, plot_h, orientation)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        context=context.unsqueeze(0),  # (1, 15) — broadcast over nodes in batch
        num_nodes=len(rooms),
    )

    if target_coords is not None:
        data.y = torch.tensor(target_coords, dtype=torch.float)  # (N, 4)

    return data


# ──────────────────────────────────────────────────────────────────────────────
# GNN Layout Model
# ──────────────────────────────────────────────────────────────────────────────
class GNNLayoutModel(nn.Module):
    """
    Graph Attention Network that predicts room polygon coordinates.

    Input:
      x           : (N_total, 12) — node features across all graphs in batch
      edge_index  : (2, E_total)  — graph edges
      edge_attr   : (E_total, 2)  — edge features
      batch       : (N_total,)    — batch assignment vector
      context     : (B, 15)       — plot context per graph

    Output:
      coords      : (N_total, 4)  — [x_norm, y_norm, w_norm, h_norm] in (0,1)
    """

    def __init__(
        self,
        node_in_dim:  int = 12,
        context_dim:  int = 15,
        hidden_dim:   int = 64,
        gat_heads:    int = 4,
        edge_dim:     int = 2,
        dropout:      float = 0.1,
    ):
        super().__init__()
        if not GEO_AVAILABLE:
            raise RuntimeError("torch_geometric required")

        self.dropout = dropout

        # Node embedding
        self.node_embed = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
        )

        # GAT layers
        gat_out = hidden_dim * gat_heads  # 256
        self.gat1 = GATConv(hidden_dim, hidden_dim, heads=gat_heads,
                             edge_dim=edge_dim, dropout=dropout, concat=True)
        self.norm1 = nn.LayerNorm(gat_out)

        self.gat2 = GATConv(gat_out, hidden_dim, heads=gat_heads,
                             dropout=dropout, concat=True)
        self.norm2 = nn.LayerNorm(gat_out)

        self.gat3 = GATConv(gat_out, hidden_dim, heads=1,
                             dropout=dropout, concat=False)
        self.norm3 = nn.LayerNorm(hidden_dim)

        # Plot context embedding
        self.context_embed = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        # Final coordinate prediction head
        self.coord_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 4),  # [x, y, w, h]
            nn.Sigmoid(),              # normalize to (0, 1)
        )

    def forward(self, x, edge_index, edge_attr, batch, context):
        """
        x           : (N_total, 12)
        edge_index  : (2, E_total)
        edge_attr   : (E_total, 2)
        batch       : (N_total,)
        context     : (B, 15)  — one context vector per graph in batch
        Returns     : (N_total, 4)
        """
        # Node embedding
        h = self.node_embed(x)                            # (N, 64)

        # GAT layer 1
        h = self.gat1(h, edge_index, edge_attr=edge_attr) # (N, 256)
        h = self.norm1(h)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)

        # GAT layer 2
        h = self.gat2(h, edge_index)                      # (N, 256)
        h = self.norm2(h)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)

        # GAT layer 3
        h = self.gat3(h, edge_index)                      # (N, 64)
        h = self.norm3(h)
        h = F.elu(h)

        # Broadcast plot context to each node
        ctx = self.context_embed(context)                 # (B, 64)
        ctx_per_node = ctx[batch]                         # (N_total, 64)

        # Concatenate node rep + context → predict coords
        combined = torch.cat([h, ctx_per_node], dim=-1)   # (N, 128)
        coords   = self.coord_head(combined)              # (N, 4)

        return coords  # [x_norm, y_norm, w_norm, h_norm]


# ──────────────────────────────────────────────────────────────────────────────
# Loss Functions
# ──────────────────────────────────────────────────────────────────────────────
def coord_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """L1 loss on (x, y, w, h) coordinates."""
    return F.l1_loss(pred, target)


def overlap_penalty(pred: torch.Tensor, batch: torch.Tensor,
                    weight: float = 0.5) -> torch.Tensor:
    """
    Soft penalty for overlapping rooms within each graph.
    Uses differentiable IoU approximation.
    """
    total_penalty = torch.tensor(0.0, device=pred.device)
    unique_graphs = batch.unique()

    for g in unique_graphs:
        mask  = batch == g
        rooms = pred[mask]  # (N_g, 4) — [x, y, w, h] normalized
        n = rooms.shape[0]
        if n < 2:
            continue

        x1 = rooms[:, 0]                  # left edge
        y1 = rooms[:, 1]                  # bottom edge
        x2 = rooms[:, 0] + rooms[:, 2]   # right edge
        y2 = rooms[:, 1] + rooms[:, 3]   # top edge

        for i in range(n):
            for j in range(i + 1, n):
                # Overlap in X direction
                ox = torch.clamp(torch.min(x2[i], x2[j]) - torch.max(x1[i], x1[j]), min=0)
                # Overlap in Y direction
                oy = torch.clamp(torch.min(y2[i], y2[j]) - torch.max(y1[i], y1[j]), min=0)
                total_penalty = total_penalty + ox * oy

    return weight * total_penalty / len(unique_graphs)


def vastu_penalty(pred: torch.Tensor, x_node: torch.Tensor,
                  weight: float = 0.3) -> torch.Tensor:
    """
    Penalizes rooms placed far from their Vastu-preferred zone.
    x_node[:, 10:12] = [vastu_pref_x, vastu_pref_y]
    pred[:, 0:2]     = [x_norm, y_norm]
    """
    pref_x = x_node[:, 10]  # vastu preferred x (0-1)
    pref_y = x_node[:, 11]  # vastu preferred y (0-1)
    pred_x = pred[:, 0]
    pred_y = pred[:, 1]
    dist   = (pred_x - pref_x).pow(2) + (pred_y - pref_y).pow(2)
    return weight * dist.mean()


def total_loss(pred, target, x_node, batch):
    """Combined training loss."""
    l_coord   = coord_loss(pred, target)
    l_overlap = overlap_penalty(pred, batch)
    l_vastu   = vastu_penalty(pred, x_node)
    return l_coord + l_overlap + l_vastu, {
        "coord": l_coord.item(),
        "overlap": l_overlap.item(),
        "vastu": l_vastu.item(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Inference Helper
# ──────────────────────────────────────────────────────────────────────────────
def predict_layout(
    model: GNNLayoutModel,
    rooms: list,
    plot_shape: str,
    plot_w: float,
    plot_h: float,
    orientation: str,
    device: str = "cpu",
) -> list:
    """
    Run inference: given room list → returns rooms with predicted
    x, y, width, height in feet.

    Args:
        model       : trained GNNLayoutModel
        rooms       : list of {name, type, area} dicts
        plot_shape  : one of 5 shape archetypes
        plot_w/h    : plot dimensions in feet
        orientation : compass direction
        device      : 'cpu' or 'cuda'

    Returns:
        rooms list with added x, y, width, height, vastu_zone fields
    """
    import copy
    model.eval()
    rooms = copy.deepcopy(rooms)

    data = rooms_to_graph(rooms, plot_shape, plot_w, plot_h, orientation)
    data = data.to(device)
    batch = torch.zeros(data.num_nodes, dtype=torch.long, device=device)

    with torch.no_grad():
        coords = model(
            data.x, data.edge_index, data.edge_attr,
            batch, data.context
        )  # (N, 4)

    coords = coords.cpu().numpy()
    for i, room in enumerate(rooms):
        x_n, y_n, w_n, h_n = coords[i]
        room["x"]      = round(float(x_n * plot_w), 1)
        room["y"]      = round(float(y_n * plot_h), 1)
        room["width"]  = max(5.0, round(float(w_n * plot_w), 1))
        room["height"] = max(5.0, round(float(h_n * plot_h), 1))

        # Derive Vastu zone from position
        if x_n > 0.55 and y_n > 0.55:
            room["vastu_zone"] = "NE"
        elif x_n < 0.45 and y_n > 0.55:
            room["vastu_zone"] = "NW"
        elif x_n > 0.55 and y_n < 0.45:
            room["vastu_zone"] = "SE"
        elif x_n < 0.45 and y_n < 0.45:
            room["vastu_zone"] = "SW"
        else:
            room["vastu_zone"] = "C"

    return rooms