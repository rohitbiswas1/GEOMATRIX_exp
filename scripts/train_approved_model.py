"""Offline training entrypoint for an approved GEOMATRIX historical dataset.

Usage:
  python scripts/train_approved_model.py data/historical.csv --algorithm RandomForest

The input CSV must contain:
  delayed (0/1 or true/false)
  data_classification=REAL
  validation_status=validated|approved

Model artifacts are written to geomatrix_v2/model_artifacts/ for explicit
review and deployment. This script never uploads data or enables runtime
training.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from geomatrix_v2.ml.train import train_model, InsufficientDataError


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--algorithm", choices=["RandomForest", "XGBoost"], default="RandomForest")
    args = parser.parse_args()

    rows = load_rows(args.csv_path)
    real = [r for r in rows if str(r.get("data_classification", "")).upper() == "REAL"]
    approved = [r for r in real if str(r.get("validation_status", "validated")).lower() in {"validated", "approved"}]
    print(f"Loaded {len(rows)} rows; {len(approved)} approved REAL rows eligible for training.")

    try:
        meta = train_model(approved, algorithm=args.algorithm)
    except InsufficientDataError as exc:
        print(f"TRAINING BLOCKED: {exc}")
        return 2

    print("MODEL CREATED")
    print(f"version={meta['model_version']}")
    print(f"samples={meta['n_samples']}")
    print(f"features={meta['used_features']}")
    print(f"dataset_fingerprint={meta['dataset_fingerprint']}")
    print(f"roc_auc={meta['roc_auc']}")
    print(f"cv_roc_auc_mean={meta['cv_roc_auc_mean']}")
    print(f"cv_f1_mean={meta['cv_f1_mean']}")
    print(f"regression_target_available={meta['regression_target_available']}")
    print("Review the saved metadata and artifacts before deployment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
