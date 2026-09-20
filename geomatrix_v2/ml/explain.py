"""Runtime-safe model explanations.

Uses SHAP when it is installed. Vercel does not need the heavyweight SHAP
package just to boot or serve predictions, so a truthful global feature-
importance fallback is returned when SHAP is unavailable.
"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ml.features import build_feature_vector
from ml.train import load_active_model

logger = logging.getLogger(__name__)

FEATURE_DESCRIPTIONS = {
    "land_area_ha": "Land area required for acquisition, in hectares.",
    "affected_families": "Families recorded as affected by acquisition.",
    "pending_claims": "Pending claims or objections recorded in the source system.",
    "legal_cases": "Active legal cases recorded for the project.",
    "doc_completeness_pct": "Percentage of required documentation confirmed complete.",
    "approval_pending": "Whether an approval remains pending.",
    "rr_pending": "Recorded rehabilitation and resettlement cases pending.",
    "overdue_milestones": "Acquisition milestones past their recorded deadline.",
    "compensation_pending": "Compensation marked pending or disputed.",
    "env_clearance_pending": "Environmental, forest or CRZ clearance marked pending.",
}

def _fallback_importance(
    classifier: Any,
    vector: Dict[str, float],
    used: list[str],
) -> list[dict[str, Any]]:
    importances = getattr(classifier, "feature_importances_", None)
    if importances is None:
        return []
    values = np.asarray(importances, dtype=float).reshape(-1)
    result = []
    for index, feature in enumerate(used):
        if index >= len(values):
            break
        result.append({
            "feature": feature,
            "display_name": feature.replace("_", " ").title(),
            "shap_value": round(float(values[index]), 6),
            "direction": "neutral",
            "description": FEATURE_DESCRIPTIONS.get(feature, feature),
            "feature_value": None if np.isnan(float(vector.get(feature, np.nan))) else round(float(vector[feature]), 4),
            "explanation_method": "global_feature_importance",
        })
    result.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return result

def explain_project(record: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    artifacts = load_active_model()
    if artifacts is None:
        return None
    classifier, _, preprocessor, meta = artifacts

    try:
        vector = build_feature_vector(record, strict=False)
        used = list(meta["used_features"])
        frame = pd.DataFrame([[vector.get(feature) for feature in used]], columns=used)
        transformed = preprocessor.transform(frame)

        try:
            import shap
            explainer = shap.TreeExplainer(classifier)
            raw = explainer.shap_values(transformed)
            if isinstance(raw, list):
                values = np.asarray(raw[1] if len(raw) > 1 else raw[0])[0]
            else:
                arr = np.asarray(raw)
                values = arr[0, :, 1] if arr.ndim == 3 else arr[0]

            result = []
            for index, feature in enumerate(used):
                value = float(values[index])
                result.append({
                    "feature": feature,
                    "display_name": feature.replace("_", " ").title(),
                    "shap_value": round(value, 6),
                    "direction": "up" if value > 0 else "down" if value < 0 else "neutral",
                    "description": FEATURE_DESCRIPTIONS.get(feature, feature),
                    "feature_value": None if np.isnan(float(vector.get(feature, np.nan))) else round(float(vector[feature]), 4),
                    "explanation_method": "shap",
                })
            result.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
            return result
        except ImportError:
            logger.info("SHAP not installed; serving global feature-importance explanation.")
            return _fallback_importance(classifier, vector, used)

    except Exception:
        logger.exception("Model explanation failed")
        return None
