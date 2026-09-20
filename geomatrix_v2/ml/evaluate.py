"""Model evaluation/status utilities."""
from typing import Any, Dict
from .train import load_active_model

def get_model_status() -> Dict[str, Any]:
    artifacts = load_active_model()
    if artifacts is None:
        return {
            "trained": False,
            "message": "No validated model is deployed.",
            "algorithm": None,
            "trained_at": None,
            "n_samples": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "roc_auc": None,
            "accuracy": None,
            "rmse": None,
            "feature_names": None,
            "feature_importance": None,
            "cv_folds": None,
            "cv_roc_auc_mean": None,
            "cv_roc_auc_std": None,
            "cv_f1_mean": None,
            "cv_f1_std": None,
            "n_unique_classes": None,
            "class_counts": None,
        }
    _, _, _, meta = artifacts
    return {
        "trained": True,
        "message": f"Validated model active — trained on {meta['n_samples']} approved real records.",
        "algorithm": meta.get("algorithm"),
        "trained_at": meta.get("trained_at"),
        "n_samples": meta.get("n_samples"),
        "precision": meta.get("precision"),
        "recall": meta.get("recall"),
        "f1_score": meta.get("f1_score"),
        "roc_auc": meta.get("roc_auc"),
        "accuracy": meta.get("accuracy"),
        "rmse": meta.get("rmse"),
        "feature_names": meta.get("feature_names"),
        "feature_importance": meta.get("feature_importance"),
        "cv_folds": meta.get("cv_folds"),
        "cv_roc_auc_mean": meta.get("cv_roc_auc_mean"),
        "cv_roc_auc_std": meta.get("cv_roc_auc_std"),
        "cv_f1_mean": meta.get("cv_f1_mean"),
        "cv_f1_std": meta.get("cv_f1_std"),
        "model_version": meta.get("model_version"),
        "n_unique_classes": meta.get("n_unique_classes"),
        "class_counts": meta.get("class_counts"),
        "dataset_fingerprint": meta.get("dataset_fingerprint"),
        "regression_target_available": meta.get("regression_target_available"),
    }
