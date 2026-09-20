"""Canonical feature engineering for GEOMATRIX.

No model feature is silently fabricated. Missing required values are surfaced
and training/prediction can be blocked rather than inventing data.
"""
from typing import Any
import pandas as pd

FEATURE_COLUMNS = [
    "land_area_ha",
    "affected_families",
    "pending_claims",
    "legal_cases",
    "doc_completeness_pct",
    "approval_pending",
    "rr_pending",
    "overdue_milestones",
    "compensation_pending",
    "env_clearance_pending",
]
LABEL_COLUMN = "delayed"
REGRESSION_LABEL = "actual_delay_days"

PREDICTION_REQUIRED_FIELDS = [
    "land_required",
    "affected_families",
    "current_stage",
    "doc_completeness_pct",
    "objection_count",
    "legal_case_count",
    "rr_status",
    "approval_pending",
    "overdue_milestones",
    "compensation_status",
]

def _first_present(record: dict[str, Any], *names: str):
    for name in names:
        value = record.get(name)
        if value is not None and value != "":
            return value
    return None

def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _to_bool01(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text in {"true", "yes", "1", "pending", "disputed"}:
        return 1.0
    if text in {"false", "no", "0", "completed", "settled", "granted", "na"}:
        return 0.0
    return None

def _status_pending(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return 1.0 if str(value).strip().lower() in {"pending", "disputed"} else 0.0

def build_feature_vector(record: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float | None] = {
        "land_area_ha": _to_float(_first_present(record, "land_area_ha", "land_required")),
        "affected_families": _to_float(_first_present(record, "affected_families")),
        "pending_claims": _to_float(_first_present(record, "pending_claims", "objection_count")),
        "legal_cases": _to_float(_first_present(record, "legal_cases", "legal_case_count")),
        "doc_completeness_pct": _to_float(_first_present(record, "doc_completeness_pct")),
        "approval_pending": _to_bool01(record.get("approval_pending")),
        "rr_pending": (
            _to_float(_first_present(record, "rr_pending"))
            if not isinstance(_first_present(record, "rr_pending"), str)
            else _status_pending(_first_present(record, "rr_pending"))
        ),
        "overdue_milestones": _to_float(_first_present(record, "overdue_milestones")),
        "compensation_pending": _to_bool01(
            _first_present(record, "compensation_pending", "compensation_status")
        ),
        "env_clearance_pending": 1.0 if any(
            _status_pending(record.get(field)) == 1.0
            for field in ("env_clearance_status", "forest_clearance_status", "crz_status")
            if record.get(field) not in (None, "")
        ) else 0.0,
    }
    missing = [name for name, value in values.items() if value is None]
    if missing:
        raise ValueError(f"Missing model features: {', '.join(missing)}")
    return {name: float(value) for name, value in values.items()}

def validate_prediction_inputs(record: dict[str, Any]) -> list[str]:
    return [
        field for field in PREDICTION_REQUIRED_FIELDS
        if record.get(field) is None or record.get(field) == ""
    ]

def build_feature_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [build_feature_vector(record) for record in records],
        columns=FEATURE_COLUMNS,
    )
