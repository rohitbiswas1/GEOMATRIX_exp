"""Canonical feature engineering for Geomatrix ML."""

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
]


def _first_present(record: dict[str, Any], *names: str):
    for name in names:
        value = record.get(name)
        if value is not None and value != "":
            return value
    return None


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_bool01(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value is None or value == "":
        return default
    text = str(value).strip().lower()
    return 1.0 if text in {"true", "yes", "1", "pending", "disputed"} else 0.0


def build_feature_vector(record: dict[str, Any]) -> dict[str, float]:
    land = _to_float(_first_present(record, "land_area_ha", "land_required"))
    families = _to_float(_first_present(record, "affected_families"))
    claims = _to_float(_first_present(record, "pending_claims", "objection_count"))
    legal = _to_float(_first_present(record, "legal_cases", "legal_case_count"))
    doc = _to_float(_first_present(record, "doc_completeness_pct"))
    rr_raw = _first_present(record, "rr_pending", "rr_status")
    rr = _to_bool01(rr_raw) if isinstance(rr_raw, (bool, str)) else (_to_float(rr_raw, 0.0) or 0.0)
    approval = _to_bool01(record.get("approval_pending"), 0.0)
    overdue = _to_float(_first_present(record, "overdue_milestones"), 0.0) or 0.0
    comp = _to_bool01(_first_present(record, "compensation_pending", "compensation_status"), 0.0)
    env = any(
        str(_first_present(record, field) or "").strip().lower() == "pending"
        for field in ("env_clearance_status", "forest_clearance_status", "crz_status")
    )

    values = {
        "land_area_ha": land,
        "affected_families": families,
        "pending_claims": claims,
        "legal_cases": legal,
        "doc_completeness_pct": doc,
        "approval_pending": approval,
        "rr_pending": rr,
        "overdue_milestones": overdue,
        "compensation_pending": 1.0 if env is False and comp else 0.0,
        "env_clearance_pending": 1.0 if env else 0.0,
    }

    missing = [k for k, v in values.items() if v is None]
    if missing:
        raise ValueError(f"Missing model features: {', '.join(missing)}")

    return {k: float(v) for k, v in values.items()}


def validate_prediction_inputs(record: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in PREDICTION_REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or value == "" or value == []:
            missing.append(field)
    return missing


def build_feature_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [build_feature_vector(r) for r in records],
        columns=FEATURE_COLUMNS,
    )
