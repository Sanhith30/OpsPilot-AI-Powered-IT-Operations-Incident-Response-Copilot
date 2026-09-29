"""
Independent Machine Learning Validation & Holdout Benchmark for OpsPilot.

Evaluates the trained regularized Random Forest model against a strictly separated,
independent holdout dataset (seed 9999) with zero data leakage.

Computes:
1. Macro & Weighted F1-Scores
2. Multi-class ROC-AUC (One-vs-Rest)
3. Confusion Matrix and per-class Precision/Recall
4. Calibration metrics (Brier Score / Multi-class Log Loss)
5. Micro-benchmark inference latency (p50, p95, p99)
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.ai.risk.ml_predictor import MLRiskPredictor, CLASSES
from app.ai.risk.ml_features import FEATURE_NAMES
from app.ai.risk.train_model import generate_independent_dataset


def evaluate_independent_holdout(n_samples: int = 500, random_seed: int = 9999) -> dict:
    print("=" * 65)
    print("OpsPilot ML Risk Predictor — Independent Holdout Evaluation")
    print(f"Dataset: {n_samples} independent holdout samples (Random Seed: {random_seed})")
    print("=" * 65)

    predictor = MLRiskPredictor()
    assert predictor._loaded, "ML model failed to load!"
    model = predictor._model

    # Set seeds for generation
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Generate independent holdout dataset
    X, y_true = generate_independent_dataset(n_samples=n_samples)

    # Predict batch
    t_start = time.perf_counter()
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)
    total_time_ms = (time.perf_counter() - t_start) * 1000

    # Individual latency micro-benchmarking
    latencies_ms = []
    for row in X:
        t0 = time.perf_counter()
        _ = model.predict_proba([row])
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    p50_lat = np.percentile(latencies_ms, 50)
    p95_lat = np.percentile(latencies_ms, 95)
    p99_lat = np.percentile(latencies_ms, 99)

    # Metrics
    acc = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, average="weighted")
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    roc_auc = roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro")

    # Per-class metrics
    per_class = {}
    for i, cls_name in enumerate(CLASSES):
        y_true_binary = (y_true == i).astype(int)
        y_prob_cls = y_prob[:, i]
        brier = brier_score_loss(y_true_binary, y_prob_cls)
        prec = precision_score(y_true, y_pred, labels=[i], average="macro", zero_division=0)
        rec = recall_score(y_true, y_pred, labels=[i], average="macro", zero_division=0)
        f1_cls = f1_score(y_true, y_pred, labels=[i], average="macro", zero_division=0)

        per_class[cls_name] = {
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1_cls), 4),
            "brier_score": round(float(brier), 4),
        }

    report = {
        "holdout_samples": n_samples,
        "random_seed": random_seed,
        "accuracy": round(float(acc), 4),
        "balanced_accuracy": round(float(bal_acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "roc_auc_ovr": round(float(roc_auc), 4),
        "confusion_matrix": cm.tolist(),
        "classes": CLASSES,
        "per_class": per_class,
        "latency_benchmark_ms": {
            "p50": round(float(p50_lat), 3),
            "p95": round(float(p95_lat), 3),
            "p99": round(float(p99_lat), 3),
            "batch_500_total_ms": round(float(total_time_ms), 2),
        },
    }

    print(f"\nOverall Performance:")
    print(f"  Accuracy:          {acc * 100:.2f}%")
    print(f"  Balanced Accuracy: {bal_acc * 100:.2f}%")
    print(f"  Macro F1-Score:    {macro_f1:.4f}")
    print(f"  Weighted F1-Score: {weighted_f1:.4f}")
    print(f"  ROC-AUC (OvR):     {roc_auc:.4f}")

    print(f"\nConfusion Matrix (Rows: True, Cols: Pred):")
    print(f"          LOW  MEDIUM  HIGH")
    for cls_name, row in zip(CLASSES, cm):
        print(f"  {cls_name:6} {row[0]:4d}   {row[1]:4d}  {row[2]:4d}")

    print(f"\nPer-Class Metrics:")
    for cls_name, m in per_class.items():
        print(f"  {cls_name:6} -> Precision: {m['precision']:.3f} | Recall: {m['recall']:.3f} | F1: {m['f1_score']:.3f} | Brier: {m['brier_score']:.3f}")

    print(f"\nInference Latency:")
    print(f"  p50: {p50_lat:.3f} ms | p95: {p95_lat:.3f} ms | p99: {p99_lat:.3f} ms")

    return report


if __name__ == "__main__":
    evaluate_independent_holdout()
