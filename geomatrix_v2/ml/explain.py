"""SHAP explanations for the deployed validated classifier."""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import shap

from .features import FEATURE_COLUMNS, build_feature_vector
from .train import load_active_model

logger = logging.getLogger(__name__)

FEATURE_DESCRIPTIONS = {
    "land_area_ha": "Land area required for acquisition, in hectares.",
    "affected_families": "Families recorded as affected by acquisition.",
    "pending_claims": "Pending claims/objections recorded in the source system.",
    "legal_cases": "Active legal cases recorded for the project.",
    "doc_completeness_pct": "Percentage of required documentation confirmed complete.",
    "approval_pending": "Whether an approval remains pending.",
    "rr_pending": "Recorded rehabilitation and resettlement cases pending.",
    "overdue_milestones": "Acquisition milestones past their recorded deadline.",
    "compensation_pending": "Compensation marked pending or disputed.",
    "env_clearance_pending": "Environmental, forest or CRZ clearance marked pending.",
}

def explain_project(record: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    artifacts = load_active_model()
    if artifacts is None:
        return None
    classifier, _, scaler, _ = artifacts
    try:
        vector = build_feature_vector(record)
        X = np.asarray([[vector[column] for column in FEATURE_COLUMNS]], dtype=float)
        X_scaled = scaler.transform(X)
        explainer = shap.TreeExplainer(classifier)
        raw = explainer.shap_values(X_scaled)

        if isinstance(raw, list):
            if len(raw) == 2:
                values = np.asarray(raw[1])[0]
            else:
                values = np.asarray(raw)[0]
        else:
            arr = np.asarray(raw)
            if arr.ndim == 3:
                values = arr[0, :, 1]
            elif arr.ndim == 2:
                values = arr[0]
            else:
                values = arr

        result: list[dict[str, Any]] = []
        for index, feature in enumerate(FEATURE_COLUMNS):
            value = float(values[index])
            result.append({
                "feature": feature,
                "display_name": feature.replace("_", " ").title(),
                "shap_value": round(value, 6),
                "direction": "up" if value > 0 else "down",
                "description": FEATURE_DESCRIPTIONS[feature],
                "feature_value": round(float(vector[feature]), 4),
            })
        result.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
        return result
    except Exception:
        logger.exception("SHAP explanation failed")
        return None
