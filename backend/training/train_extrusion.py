"""
ZYNORA-ML — 3D Extrusion Model Training Script
===============================================
Trains ExtrusionModel on Structured3D dataset.
Learns wall heights, slab thickness, ceiling types from real 3D house data.

USAGE:
  python train_extrusion.py --data_dir ./data/structured3d --epochs 80
"""

import os, sys, argparse, time, json
from pathlib import Path

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import StepLR

sys.path.insert(0, str(Path(__file__).parent.parent))
from training.models.extrusion_model import ExtrusionModel, extrusion_loss
from training.datasets.structured3d_dataset import Structured3DDataset


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data_dir", default="backend/data/structured3d")
    p.add_argument("--save_dir", default="backend/models")
    p.add_argument("--epochs",   type=int, default=80)
    p.add_argument("--batch",    type=int, default=128)
    p.add_argument("--lr",       type=float, default=1e-3)
    p.add_argument("--patience", type=int, default=10)
    p.add_argument("--device",   default="auto")
    return p.parse_args()


def collate_fn(batch):
    xs      = torch.stack([b[0] for b in batch])
    targets = {
        "wall_height_norm": torch.stack([b[1]["wall_height_norm"] for b in batch]),
        "floor_thick_norm": torch.stack([b[1]["floor_thick_norm"] for b in batch]),
        "ceiling_type":     torch.stack([b[1]["ceiling_type"]     for b in batch]),
    }
    return xs, targets


def evaluate(model, loader, device):
    model.eval()
    total, n = 0.0, 0
    with torch.no_grad():
        for xs, targets in loader:
            xs = xs.to(device)
            targets = {k: v.to(device) for k, v in targets.items()}
            pred = model(xs)
            loss, _ = extrusion_loss(pred, targets)
            total += loss.item() * xs.size(0)
            n     += xs.size(0)
    return total / max(1, n)


def train():
    args   = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") \
             if args.device == "auto" else torch.device(args.device)

    print(f"\n{'='*60}")
    print(f"ZYNORA-ML :: 3D Extrusion Model Training")
    print(f"  Device : {device}")
    print(f"  Data   : {args.data_dir}")
    print(f"  Epochs : {args.epochs}  |  Batch: {args.batch}")
    print(f"{'='*60}\n")

    train_ds = Structured3DDataset(args.data_dir, split="train")
    val_ds   = Structured3DDataset(args.data_dir, split="val")
    print(f"  Train: {len(train_ds)} samples  |  Val: {len(val_ds)} samples\n")

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                              collate_fn=collate_fn, num_workers=2)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch, shuffle=False,
                              collate_fn=collate_fn, num_workers=2)

    model = ExtrusionModel().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model: ExtrusionModel  |  Parameters: {n_params:,}\n")

    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = StepLR(optimizer, step_size=20, gamma=0.5)

    best_val_loss  = float("inf")
    patience_count = 0
    save_dir       = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    history        = {"train_loss": [], "val_loss": []}

    for epoch in range(args.epochs):
        model.train()
        epoch_loss, n = 0.0, 0
        t0 = time.time()

        for xs, targets in train_loader:
            xs      = xs.to(device)
            targets = {k: v.to(device) for k, v in targets.items()}
            optimizer.zero_grad()
            pred = model(xs)
            loss, comps = extrusion_loss(pred, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * xs.size(0)
            n          += xs.size(0)

        scheduler.step()
        train_loss = epoch_loss / max(1, n)
        val_loss   = evaluate(model, val_loader, device)
        elapsed    = time.time() - t0
        is_best    = val_loss < best_val_loss
        marker     = " ← BEST" if is_best else ""

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        print(f"Epoch [{epoch+1:3d}/{args.epochs}]  "
              f"train={train_loss:.4f}  val={val_loss:.4f}  "
              f"time={elapsed:.1f}s{marker}")

        if is_best:
            best_val_loss  = val_loss
            patience_count = 0
            torch.save({
                "epoch": epoch + 1,
                "model_state":   model.state_dict(),
                "best_val_loss": best_val_loss,
            }, save_dir / "extrusion_model_best.pt")
            print(f"  ✓ Saved  (val={best_val_loss:.4f})")
        else:
            patience_count += 1
            if patience_count >= args.patience:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    print(f"\nDone. Best val loss: {best_val_loss:.4f}")
    print(f"Saved: {save_dir / 'extrusion_model_best.pt'}")

    with open(save_dir / "extrusion_history.json", "w") as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    train()
