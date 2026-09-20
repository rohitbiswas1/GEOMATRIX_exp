"""Prediction helpers. A prediction exists only when a validated trained model exists."""
import logging
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

from ml.features import build_feature_vector, FEATURE_COLUMNS
from ml.train import load_active_model

logger = logging.getLogger(__name__)


def risk_level_from_score(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Low"


def predict_project_risk(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    artifacts = load_active_model()
    if artifacts is None:
        return {
            "status": "not_trained",
            "message": "Model not trained — insufficient real labeled data.",
            "risk_score": None,
            "risk_level": None,
            "delay_probability": None,
            "predicted_delay_days": None,
            "confidence": None,
            "model_run_id": None,
            "model_version": None,
            "prediction_generated_at": None,
        }

    clf, reg, scaler, meta = artifacts

    try:
        fv = build_feature_vector(record)
        X = pd.DataFrame([[fv[c] for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
        X_scaled = scaler.transform(X)
        proba = clf.predict_proba(X_scaled)[0]
        classes = list(getattr(clf, "classes_", [0, 1]))
        delay_idx = classes.index(1) if 1 in classes else None
        if delay_idx is None:
            raise ValueError("Active classifier does not contain the delay class.")
        delay_prob = float(np.clip(proba[delay_idx], 0.0, 1.0))
        risk_score = round(delay_prob * 100.0, 1)

        predicted_delay_days = None
        regression_target_available = bool(meta.get("regression_target_available"))
        if reg is not None and regression_target_available:
            predicted_delay_days = max(0, int(round(float(reg.predict(X_scaled)[0]))))

        roc_auc = meta.get("roc_auc")
        confidence = None if roc_auc is None else round(float(np.clip(roc_auc, 0.0, 1.0)), 4)

        return {
            "status": "ok",
            "risk_score": risk_score,
            "risk_level": risk_level_from_score(risk_score),
            "delay_probability": round(delay_prob, 4),
            "predicted_delay_days": predicted_delay_days,
            "confidence": confidence,
            "model_run_id": meta.get("run_id"),
            "model_version": meta.get("model_version"),
            "prediction_generated_at": meta.get("trained_at"),
            "message": "Prediction generated from the validated trained model.",
        }
    except Exception as exc:
        logger.error("Prediction failed: %s", exc, exc_info=True)
        return {
            "status": "error",
            "message": f"Prediction failed: {exc}",
            "risk_score": None,
            "risk_level": None,
            "delay_probability": None,
            "predicted_delay_days": None,
            "confidence": None,
            "model_run_id": None,
            "model_version": None,
            "prediction_generated_at": None,
        }
