"""
ZYNORA-ML — Local RTX 3050 Training Script
===========================================
Optimized for 4GB VRAM. Trains both models sequentially.
Run: python backend/training/train_local.py
"""

import os, sys, time, json, argparse
from pathlib import Path

# ── Setup paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent  # y:/YPS-Labs/zynora-ml
sys.path.insert(0, str(ROOT / "backend"))

import torch
print("=" * 55)
print("ZYNORA-ML — Local GPU Training")
print("=" * 55)
print(f"PyTorch : {torch.__version__}")
print(f"CUDA    : {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU     : {torch.cuda.get_device_name(0)}")
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"VRAM    : {vram:.1f} GB")
    if vram < 5:
        print("INFO    : <5GB VRAM detected — using small batch mode")
print("=" * 55)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── 4GB VRAM-safe hyperparams ──────────────────────────────────────────────────
BATCH_SIZE  = 4      # small batch for 4GB (Colab uses 32)
HIDDEN_DIM  = 32     # smaller model for 4GB (Colab uses 64)
GAT_HEADS   = 2      # fewer heads for 4GB (Colab uses 4)
LR          = 1e-3
EPOCHS_GNN  = 80
EPOCHS_EXT  = 60
PATIENCE    = 10
SAVE_DIR    = ROOT / "backend" / "models"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 1: GNN Layout Model
# ════════════════════════════════════════════════════════════════════════════════
def train_gnn():
    print("\n" + "─" * 55)
    print("STAGE 1: GNN Layout Model")
    print("─" * 55)

    try:
        from torch_geometric.loader import DataLoader
    except ImportError:
        print("\nERROR: torch_geometric not installed.")
        print("Run: pip install torch-geometric torch-scatter torch-sparse torch-cluster")
        print("     -f https://data.pyg.org/whl/torch-2.4.0+cu121.html")
        return False

    from training.models.gnn_layout_model import GNNLayoutModel, total_loss
    from training.datasets.resplan_dataset import ResPlanDataset
    import torch.optim as optim
    from torch.optim.lr_scheduler import CosineAnnealingLR

    data_dir = ROOT / "backend" / "data" / "resplan"
    train_ds = ResPlanDataset(str(data_dir), split="train")
    val_ds   = ResPlanDataset(str(data_dir), split="val")
    print(f"Dataset : {len(train_ds)} train  |  {len(val_ds)} val")
    print(f"Batch   : {BATCH_SIZE}  |  Hidden: {HIDDEN_DIM}  |  Heads: {GAT_HEADS}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model     = GNNLayoutModel(hidden_dim=HIDDEN_DIM, gat_heads=GAT_HEADS).to(DEVICE)
    n_params  = sum(p.numel() for p in model.parameters())
    print(f"Params  : {n_params:,}\n")

    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS_GNN, eta_min=1e-5)

    best_val, patience_cnt = float("inf"), 0
    history = []

    for epoch in range(EPOCHS_GNN):
        # ── Train ──
        model.train()
        tl, tn = 0.0, 0
        t0 = time.time()
        for bd in train_loader:
            if bd is None: continue
            bd = bd.to(DEVICE)
            optimizer.zero_grad()
            pred = model(bd.x, bd.edge_index, bd.edge_attr,
                         bd.batch, bd.context.squeeze(1))
            loss, _ = total_loss(pred, bd.y, bd.x, bd.batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            tl += loss.item() * bd.num_graphs
            tn += bd.num_graphs

            # Free VRAM aggressively on 4GB
            del bd, pred, loss
            if DEVICE.type == "cuda":
                torch.cuda.empty_cache()

        scheduler.step()

        # ── Validate ──
        model.eval()
        vl, vn = 0.0, 0
        with torch.no_grad():
            for bd in val_loader:
                if bd is None: continue
                bd = bd.to(DEVICE)
                p = model(bd.x, bd.edge_index, bd.edge_attr,
                          bd.batch, bd.context.squeeze(1))
                l, _ = total_loss(p, bd.y, bd.x, bd.batch)
                vl += l.item() * bd.num_graphs
                vn += bd.num_graphs

        tr_l = tl / max(1, tn)
        v_l  = vl / max(1, vn)
        elapsed = time.time() - t0
        history.append({"epoch": epoch+1, "train": tr_l, "val": v_l})

        mark = " ← BEST" if v_l < best_val else ""
        print(f"[{epoch+1:3d}/{EPOCHS_GNN}]  "
              f"train={tr_l:.4f}  val={v_l:.4f}  "
              f"({elapsed:.0f}s){mark}")

        if v_l < best_val:
            best_val    = v_l
            patience_cnt = 0
            torch.save({
                "epoch":       epoch + 1,
                "model_state": model.state_dict(),
                "best_val":    best_val,
                "hidden_dim":  HIDDEN_DIM,
                "gat_heads":   GAT_HEADS,
            }, SAVE_DIR / "gnn_layout_best.pt")
            print(f"  ✓ Saved gnn_layout_best.pt  (val={best_val:.4f})")
        else:
            patience_cnt += 1
            if patience_cnt >= PATIENCE:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    with open(SAVE_DIR / "gnn_layout_history.json", "w") as f:
        json.dump(history, f, indent=2)

    size_mb = (SAVE_DIR / "gnn_layout_best.pt").stat().st_size / 1e6
    print(f"\nGNN Layout done. Best val: {best_val:.4f}  |  File: {size_mb:.1f} MB")
    return True


# ════════════════════════════════════════════════════════════════════════════════
# STAGE 2: 3D Extrusion Model
# ════════════════════════════════════════════════════════════════════════════════
def train_extrusion():
    print("\n" + "─" * 55)
    print("STAGE 2: 3D Extrusion Model")
    print("─" * 55)

    from torch.utils.data import DataLoader as TorchLoader
    from training.models.extrusion_model import ExtrusionModel, extrusion_loss
    from training.datasets.structured3d_dataset import Structured3DDataset
    import torch.optim as optim

    def collate(batch):
        return torch.stack([b[0] for b in batch]), {
            "wall_height_norm": torch.stack([b[1]["wall_height_norm"] for b in batch]),
            "floor_thick_norm": torch.stack([b[1]["floor_thick_norm"] for b in batch]),
            "ceiling_type":     torch.stack([b[1]["ceiling_type"]     for b in batch]),
        }

    data_dir  = ROOT / "backend" / "data" / "structured3d"
    train_ds  = Structured3DDataset(str(data_dir), split="train")
    val_ds    = Structured3DDataset(str(data_dir), split="val")
    print(f"Dataset : {len(train_ds)} train  |  {len(val_ds)} val")

    # Extrusion model is tiny — can use larger batch
    train_loader = TorchLoader(train_ds, batch_size=64, shuffle=True,
                               collate_fn=collate, num_workers=0)
    val_loader   = TorchLoader(val_ds,   batch_size=64, shuffle=False,
                               collate_fn=collate, num_workers=0)

    model     = ExtrusionModel().to(DEVICE)
    n_params  = sum(p.numel() for p in model.parameters())
    print(f"Params  : {n_params:,}\n")

    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    best_val, patience_cnt = float("inf"), 0
    history = []

    for epoch in range(EPOCHS_EXT):
        model.train()
        tl, tn = 0.0, 0
        t0 = time.time()
        for xs, tgt in train_loader:
            xs  = xs.to(DEVICE)
            tgt = {k: v.to(DEVICE) for k, v in tgt.items()}
            optimizer.zero_grad()
            loss, _ = extrusion_loss(model(xs), tgt)
            loss.backward()
            optimizer.step()
            tl += loss.item() * xs.size(0)
            tn += xs.size(0)

        model.eval()
        vl, vn = 0.0, 0
        with torch.no_grad():
            for xs, tgt in val_loader:
                xs  = xs.to(DEVICE)
                tgt = {k: v.to(DEVICE) for k, v in tgt.items()}
                l, _ = extrusion_loss(model(xs), tgt)
                vl += l.item() * xs.size(0)
                vn += xs.size(0)

        tr_l    = tl / max(1, tn)
        v_l     = vl / max(1, vn)
        elapsed = time.time() - t0
        history.append({"epoch": epoch+1, "train": tr_l, "val": v_l})

        mark = " ← BEST" if v_l < best_val else ""
        print(f"[{epoch+1:3d}/{EPOCHS_EXT}]  "
              f"train={tr_l:.4f}  val={v_l:.4f}  ({elapsed:.0f}s){mark}")

        if v_l < best_val:
            best_val     = v_l
            patience_cnt = 0
            torch.save({
                "epoch":       epoch + 1,
                "model_state": model.state_dict(),
                "best_val":    best_val,
            }, SAVE_DIR / "extrusion_model_best.pt")
            print(f"  ✓ Saved extrusion_model_best.pt")
        else:
            patience_cnt += 1
            if patience_cnt >= PATIENCE:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    with open(SAVE_DIR / "extrusion_history.json", "w") as f:
        json.dump(history, f, indent=2)

    size_mb = (SAVE_DIR / "extrusion_model_best.pt").stat().st_size / 1e6
    print(f"\nExtrusion done. Best val: {best_val:.4f}  |  File: {size_mb:.1f} MB")
    return True


# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\nStarting local training on RTX 3050...")
    print(f"Weights will be saved to: {SAVE_DIR}\n")

    t_start = time.time()
    gnn_ok  = train_gnn()
    ext_ok  = train_extrusion()
    total   = (time.time() - t_start) / 60

    print("\n" + "=" * 55)
    print("TRAINING COMPLETE")
    print(f"  GNN Layout   : {'OK' if gnn_ok else 'FAILED'}")
    print(f"  Extrusion    : {'OK' if ext_ok else 'FAILED'}")
    print(f"  Total time   : {total:.1f} minutes")
    print(f"  Models saved : {SAVE_DIR}")
    print("=" * 55)
    print("\nNext: tell Antigravity 'weights ready' to wire into Zynora!")
