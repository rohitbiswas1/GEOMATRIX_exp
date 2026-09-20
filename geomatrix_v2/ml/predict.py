"""Prediction using the deployed validated model."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ml.features import FEATURE_COLUMNS, build_feature_vector
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
            "message": "No validated model is deployed.",
            "risk_score": None,
            "risk_level": None,
            "delay_probability": None,
            "predicted_delay_days": None,
            "confidence": None,
            "imputed_features": [],
            "model_run_id": None,
            "model_version": None,
            "prediction_generated_at": None,
        }

    classifier, regressor, preprocessor, meta = artifacts
    try:
        vector = build_feature_vector(record, strict=False)
        used = list(meta["used_features"])
        missing = [feature for feature in used if np.isnan(float(vector.get(feature, np.nan)))]
        X = pd.DataFrame([[vector.get(feature) for feature in used]], columns=used)
        X_transformed = preprocessor.transform(X)
        probabilities = classifier.predict_proba(X_transformed)[0]
        classes = list(getattr(classifier, "classes_", []))
        if 1 not in classes:
            raise ValueError("Active classifier does not contain the delay class.")
        delay_probability = float(np.clip(probabilities[classes.index(1)], 0.0, 1.0))
        certainty = float(np.clip(np.max(probabilities), 0.0, 1.0))

        predicted_delay_days = None
        if regressor is not None and bool(meta.get("regression_target_available")):
            predicted_delay_days = max(0, int(round(float(regressor.predict(X_transformed)[0]))))

        now = datetime.utcnow().isoformat()
        return {
            "status": "ok",
            "risk_score": round(delay_probability * 100.0, 1),
            "risk_level": risk_level_from_score(delay_probability * 100.0),
            "delay_probability": round(delay_probability, 4),
            "predicted_delay_days": predicted_delay_days,
            "confidence": round(certainty, 4),
            "imputed_features": missing,
            "model_run_id": meta.get("run_id"),
            "model_version": meta.get("model_version"),
            "prediction_generated_at": now,
            "message": (
                "Prediction generated from the deployed validated model."
                + (f" Missing source fields were imputed by the approved training pipeline: {', '.join(missing)}." if missing else "")
            ),
        }
    except Exception as exc:
        logger.error("Prediction failed", exc_info=True)
        return {
            "status": "error",
            "message": f"Prediction failed: {exc}",
            "risk_score": None,
            "risk_level": None,
            "delay_probability": None,
            "predicted_delay_days": None,
            "confidence": None,
            "imputed_features": [],
            "model_run_id": None,
            "model_version": None,
            "prediction_generated_at": None,
        }
