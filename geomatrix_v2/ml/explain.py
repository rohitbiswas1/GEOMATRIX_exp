"""SHAP explanations for the deployed validated classifier."""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import shap

from .features import build_feature_vector
from .train import load_active_model

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

def explain_project(record: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    artifacts = load_active_model()
    if artifacts is None:
        return None
    classifier, _, preprocessor, meta = artifacts
    try:
        vector = build_feature_vector(record)
        used = list(meta["used_features"])
        frame = pd.DataFrame([[vector.get(feature) for feature in used]], columns=used)
        transformed = preprocessor.transform(frame)
        explainer = shap.TreeExplainer(classifier)
        raw = explainer.shap_values(transformed)

        if isinstance(raw, list):
            values = np.asarray(raw[1] if len(raw) > 1 else raw[0])[0]
        else:
            arr = np.asarray(raw)
            values = arr[0, :, 1] if arr.ndim == 3 else arr[0]

        # Tree SHAP after add_indicator produces original features followed by
        # missingness indicators. Collapse each original feature + its indicator.
        base_feature_count = len(used)
        values = np.asarray(values, dtype=float)
        collapsed = []
        for index, feature in enumerate(used):
            shap_value = float(values[index])
            indicator_index = base_feature_count + index
            if indicator_index < len(values) and frame.iloc[0][feature] is None:
                shap_value += float(values[indicator_index])
            collapsed.append({
                "feature": feature,
                "display_name": feature.replace("_", " ").title(),
                "shap_value": round(shap_value, 6),
                "direction": "up" if shap_value > 0 else "down",
                "description": FEATURE_DESCRIPTIONS.get(feature, feature),
                "feature_value": None if vector.get(feature) is None else round(float(vector[feature]), 4),
            })

        collapsed.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
        return collapsed
    except Exception:
        logger.exception("SHAP explanation failed")
        return None
