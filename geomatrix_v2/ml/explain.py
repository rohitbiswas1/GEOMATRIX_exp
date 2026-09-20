"""Lightweight model feature-contribution explanations.

This runtime deliberately avoids the heavyweight SHAP package so the FastAPI
function remains deployable on Vercel. The contribution value is the change
in delayed-class probability when the feature is replaced by the training
baseline (median/imputation behavior is preserved by the fitted preprocessor).
It is model-derived evidence, not a causal effect.
"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

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
        vector = build_feature_vector(record, strict=False)
        used = list(meta["used_features"])
        current = np.asarray(
            [[vector.get(feature, np.nan) for feature in used]],
            dtype=float,
        )
        transformed = preprocessor.transform(
            pd.DataFrame(current, columns=used)
        )

        classes = list(getattr(classifier, "classes_", []))
        if 1 not in classes:
            raise ValueError("Active classifier does not contain the delay class.")
        delay_index = classes.index(1)

        base_probability = float(classifier.predict_proba(transformed)[0, delay_index])
        results: list[dict[str, Any]] = []

        for index, feature in enumerate(used):
            test = current.copy()
            baseline = getattr(preprocessor.named_steps["imputer"], "statistics_", np.array([]))
            if index >= len(baseline) or np.isnan(float(baseline[index])):
                continue
            test[0, index] = float(baseline[index])
            transformed_test = preprocessor.transform(
                pd.DataFrame(test, columns=used)
            )
            replaced_probability = float(
                classifier.predict_proba(transformed_test)[0, delay_index]
            )
            contribution = base_probability - replaced_probability

            value = vector.get(feature)
            results.append({
                "feature": feature,
                "display_name": feature.replace("_", " ").title(),
                "shap_value": round(contribution, 6),
                "direction": "up" if contribution > 0 else "down",
                "description": FEATURE_DESCRIPTIONS.get(feature, feature),
                "feature_value": (
                    None
                    if value is None or np.isnan(float(value))
                    else round(float(value), 4)
                ),
                "explanation_method": "baseline_probability_delta",
            })

        results.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
        return results
    except Exception:
        logger.exception("Feature contribution explanation failed")
        return None
