"""
ZYNORA-ML — GNN Layout Model Training Script
============================================
Trains the GNNLayoutModel on ResPlan + RPLAN datasets.
Run on Kaggle (free T4 GPU) or locally if you have >=6GB VRAM.

USAGE:
  python train_layout.py --data_dir ./data/resplan --epochs 100 --batch 32
  python train_layout.py --data_dir ./data/resplan --resume ./checkpoints/gnn_layout_best.pt
"""

import os
import sys
import argparse
import time
from pathlib import Path

import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

try:
    from torch_geometric.loader import DataLoader
    from torch_geometric.data import Batch
    GEO_AVAILABLE = True
except ImportError:
    GEO_AVAILABLE = False
    print("[ERROR] torch_geometric not installed.")
    print("  Run: pip install torch-geometric torch-scatter torch-sparse torch-cluster")
    sys.exit(1)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from training.models.gnn_layout_model import GNNLayoutModel, total_loss
from training.datasets.resplan_dataset import ResPlanDataset


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data_dir",   default="backend/data/resplan",  help="ResPlan data directory")
    p.add_argument("--save_dir",   default="backend/models",        help="Where to save weights")
    p.add_argument("--epochs",     type=int, default=100)
    p.add_argument("--batch",      type=int, default=32)
    p.add_argument("--lr",         type=float, default=1e-3)
    p.add_argument("--patience",   type=int, default=12,            help="Early stop patience")
    p.add_argument("--hidden",     type=int, default=64,            help="GNN hidden dim")
    p.add_argument("--heads",      type=int, default=4,             help="GAT attention heads")
    p.add_argument("--resume",     default=None,                    help="Resume from checkpoint")
    p.add_argument("--device",     default="auto")
    return p.parse_args()


def evaluate(model, loader, device):
    model.eval()
    total, n = 0.0, 0
    with torch.no_grad():
        for batch_data in loader:
            if batch_data is None:
                continue
            batch_data = batch_data.to(device)
            pred = model(
                batch_data.x, batch_data.edge_index, batch_data.edge_attr,
                batch_data.batch, batch_data.context.squeeze(1)
            )
            loss, _ = total_loss(pred, batch_data.y, batch_data.x, batch_data.batch)
            total += loss.item() * batch_data.num_graphs
            n     += batch_data.num_graphs
    return total / max(1, n)


def train():
    args = parse_args()

    # Device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    print(f"\n{'='*60}")
    print(f"ZYNORA-ML :: GNN Layout Training")
    print(f"  Device  : {device}")
    if device.type == "cuda":
        print(f"  GPU     : {torch.cuda.get_device_name(0)}")
        print(f"  VRAM    : {torch.cuda.get_device_properties(0).total_memory // 1e9:.1f} GB")
    print(f"  Data    : {args.data_dir}")
    print(f"  Epochs  : {args.epochs}  |  Batch: {args.batch}  |  LR: {args.lr}")
    print(f"{'='*60}\n")

    # Datasets
    print("Loading datasets...")
    train_ds = ResPlanDataset(args.data_dir, split="train")
    val_ds   = ResPlanDataset(args.data_dir, split="val")
    print(f"  Train: {len(train_ds)} plans  |  Val: {len(val_ds)} plans\n")

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch, shuffle=False, num_workers=0)

    # Model
    model = GNNLayoutModel(hidden_dim=args.hidden, gat_heads=args.heads).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model: GNNLayoutModel  |  Parameters: {n_params:,}\n")

    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)

    # Resume
    start_epoch  = 0
    best_val_loss = float("inf")
    patience_count = 0

    if args.resume and Path(args.resume).exists():
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state"])
        optimizer.load_state_dict(ckpt["optim_state"])
        start_epoch  = ckpt.get("epoch", 0)
        best_val_loss = ckpt.get("best_val_loss", float("inf"))
        print(f"Resumed from {args.resume} at epoch {start_epoch}\n")

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # ── Training Loop ──────────────────────────────────────────────────────────
    history = {"train_loss": [], "val_loss": []}

    for epoch in range(start_epoch, args.epochs):
        model.train()
        epoch_loss, n_graphs = 0.0, 0
        t0 = time.time()

        for batch_data in train_loader:
            if batch_data is None:
                continue
            batch_data = batch_data.to(device)

            optimizer.zero_grad()
            pred = model(
                batch_data.x, batch_data.edge_index, batch_data.edge_attr,
                batch_data.batch, batch_data.context.squeeze(1)
            )
            loss, components = total_loss(
                pred, batch_data.y, batch_data.x, batch_data.batch
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            epoch_loss += loss.item() * batch_data.num_graphs
            n_graphs   += batch_data.num_graphs

        scheduler.step()

        train_loss = epoch_loss / max(1, n_graphs)
        val_loss   = evaluate(model, val_loader, device)
        elapsed    = time.time() - t0

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        is_best = val_loss < best_val_loss
        marker  = " ← BEST" if is_best else ""

        print(f"Epoch [{epoch+1:3d}/{args.epochs}]  "
              f"train={train_loss:.4f}  val={val_loss:.4f}  "
              f"lr={scheduler.get_last_lr()[0]:.2e}  "
              f"time={elapsed:.1f}s{marker}")

        if is_best:
            best_val_loss  = val_loss
            patience_count = 0
            torch.save({
                "epoch":          epoch + 1,
                "model_state":    model.state_dict(),
                "optim_state":    optimizer.state_dict(),
                "best_val_loss":  best_val_loss,
                "args":           vars(args),
            }, save_dir / "gnn_layout_best.pt")
            print(f"  ✓ Saved best model  (val_loss={best_val_loss:.4f})")
        else:
            patience_count += 1
            if patience_count >= args.patience:
                print(f"\nEarly stopping at epoch {epoch+1} (no improvement for {args.patience} epochs)")
                break

        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            torch.save({
                "epoch": epoch + 1,
                "model_state":   model.state_dict(),
                "optim_state":   optimizer.state_dict(),
                "best_val_loss": best_val_loss,
            }, save_dir / f"gnn_layout_epoch{epoch+1}.pt")

    print(f"\nTraining complete. Best val loss: {best_val_loss:.4f}")
    print(f"Best model saved to: {save_dir / 'gnn_layout_best.pt'}")

    # Save training history
    import json
    with open(save_dir / "gnn_layout_history.json", "w") as f:
        json.dump(history, f, indent=2)
    print(f"History saved to: {save_dir / 'gnn_layout_history.json'}")


if __name__ == "__main__":
    train()
