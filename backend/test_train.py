"""Quick test to verify full Bengaluru dataset trains and returns good R²"""
import sys, os, glob
sys.path.insert(0, os.path.abspath("."))

# Delete any cached .joblib so we force a fresh training run
for f in glob.glob("backend/models/*.joblib"):
    os.remove(f)
    print(f"Removed cached model: {f}")

# Reset singleton so a fresh instance is created
from backend.app.ml import model_registry as mr
mr.ModelRegistry._instance = None

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

registry = mr.ModelRegistry.get_instance()
registry.startup_train()

print()
print("=" * 55)
print("  ZYNORA-ML Training Results (Full Bengaluru Dataset)")
print("=" * 55)
print(f"  Dataset records  : {registry.dataset_size:,}")
print(f"  Training samples : {registry.rf_training_samples:,}")
print(f"  Test samples     : {registry.rf_test_samples:,}")
print(f"  RandomForest R²  : {registry.rf_r2}   (goal: > 0.80)")
print(f"  KMeans Silhouette: {registry.kmeans_silhouette}  (goal: > 0.25)")
print()
print("  Feature Importances:")
for feat, imp in sorted(registry.rf_feature_importances.items(), key=lambda x: -x[1]):
    bar = "█" * int(imp * 40)
    print(f"    {feat:<15} {bar:<20} {imp:.3f}")
print("=" * 55)
