"""Validated, reproducible ML training for GEOMATRIX."""
import hashlib
import json
import logging
import os
import pickle
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from .features import FEATURE_COLUMNS, LABEL_COLUMN, REGRESSION_LABEL

logger = logging.getLogger(__name__)

MIN_SAMPLES = 10
MIN_REGRESSION_SAMPLES = 20
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model_artifacts"))
os.makedirs(MODEL_DIR, exist_ok=True)


class InsufficientDataError(Exception):
    """Raised when the approved dataset cannot support a valid model."""


def _clear_active_model_files() -> None:
    active = os.path.join(MODEL_DIR, "active_model.json")
    try:
        if os.path.exists(active):
            os.remove(active)
    except OSError:
        logger.warning("Unable to remove active model pointer")


def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for record in records:
        if not isinstance(record, dict) or record.get(LABEL_COLUMN) is None:
            continue
        classification = str(record.get("data_classification") or "REAL").strip().upper()
        validation = str(record.get("validation_status") or "validated").strip().lower()
        if classification != "REAL" or validation not in {"validated", "approved"}:
            continue
        out.append(record)
    return out


def _dataset_fingerprint(records: list[dict[str, Any]]) -> str:
    payload = [
        {key: record.get(key) for key in sorted(set(FEATURE_COLUMNS + [LABEL_COLUMN, REGRESSION_LABEL]))}
        for record in records
    ]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _classifier(algorithm: str):
    if algorithm == "XGBoost" and XGBOOST_AVAILABLE:
        return XGBClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            eval_metric="logloss",
            verbosity=0,
        )
    return RandomForestClassifier(
        n_estimators=250,
        max_depth=8,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def _regressor(algorithm: str):
    if algorithm == "XGBoost" and XGBOOST_AVAILABLE:
        return XGBRegressor(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            objective="reg:squarederror",
            verbosity=0,
        )
    return RandomForestRegressor(
        n_estimators=250,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )


def train_model(records: list[dict[str, Any]], algorithm: str = "RandomForest") -> Dict[str, Any]:
    records = _normalize_records(records)
    if len(records) < MIN_SAMPLES:
        raise InsufficientDataError(
            f"Only {len(records)} approved real labeled records are available. "
            f"Minimum {MIN_SAMPLES} is required."
        )

    from .features import build_feature_dataframe
    try:
        X = build_feature_dataframe(records)
    except ValueError as exc:
        raise InsufficientDataError(str(exc)) from exc

    y = np.asarray([bool(record[LABEL_COLUMN]) for record in records], dtype=bool).astype(int)
    unique_classes = np.unique(y)
    if len(unique_classes) < 2:
        raise InsufficientDataError(
            "Training rejected: both delayed and on-time real labels are required."
        )

    regression_available = (
        len(records) >= MIN_REGRESSION_SAMPLES
        and all(record.get(REGRESSION_LABEL) not in (None, "") for record in records)
    )
    y_reg = (
        np.asarray([float(record[REGRESSION_LABEL]) for record in records], dtype=float)
        if regression_available
        else None
    )

    algorithm = algorithm if algorithm in {"RandomForest", "XGBoost"} else "RandomForest"
    classifier = _classifier(algorithm)
    regressor = _regressor(algorithm) if regression_available else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    classifier.fit(X_train_scaled, y_train)

    if regressor is not None and y_reg is not None:
        train_idx, test_idx = train_test_split(
            np.arange(len(records)),
            test_size=0.2,
            random_state=42,
            stratify=y,
        )
        regressor.fit(scaler.transform(X.iloc[train_idx]), y_reg[train_idx])
        y_reg_pred = regressor.predict(scaler.transform(X.iloc[test_idx]))
        rmse = float(np.sqrt(mean_squared_error(y_reg[test_idx], y_reg_pred)))
    else:
        rmse = None

    y_pred = classifier.predict(X_test_scaled)
    classes = list(getattr(classifier, "classes_", []))
    delay_idx = classes.index(1) if 1 in classes else None
    if delay_idx is None:
        raise InsufficientDataError("Trained classifier does not contain the delay class.")
    y_prob = classifier.predict_proba(X_test_scaled)[:, delay_idx]

    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else None

    cv_folds = min(5, int(np.bincount(y).min()))
    cv_roc_auc_mean = cv_roc_auc_std = cv_f1_mean = cv_f1_std = None
    if cv_folds >= 2:
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", _classifier(algorithm)),
        ])
        try:
            cv_auc = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
            cv_f1 = cross_val_score(pipeline, X, y, cv=cv, scoring="f1")
            cv_roc_auc_mean, cv_roc_auc_std = float(cv_auc.mean()), float(cv_auc.std())
            cv_f1_mean, cv_f1_std = float(cv_f1.mean()), float(cv_f1.std())
        except Exception:
            logger.exception("Cross-validation failed")

    feature_importance = {
        feature: round(float(value), 6)
        for feature, value in zip(FEATURE_COLUMNS, classifier.feature_importances_)
    }

    run_id = str(uuid.uuid4())
    version = f"{algorithm.lower()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    clf_path = os.path.join(MODEL_DIR, f"clf_{run_id}.pkl")
    reg_path = os.path.join(MODEL_DIR, f"reg_{run_id}.pkl") if regressor is not None else None
    scaler_path = os.path.join(MODEL_DIR, f"scaler_{run_id}.pkl")
    meta_path = os.path.join(MODEL_DIR, f"meta_{run_id}.json")

    with open(clf_path, "wb") as handle:
        pickle.dump(classifier, handle)
    if regressor is not None and reg_path:
        with open(reg_path, "wb") as handle:
            pickle.dump(regressor, handle)
    with open(scaler_path, "wb") as handle:
        pickle.dump(scaler, handle)

    meta: Dict[str, Any] = {
        "run_id": run_id,
        "model_version": version,
        "algorithm": algorithm,
        "trained_at": datetime.utcnow().isoformat(),
        "n_samples": len(records),
        "n_features": len(FEATURE_COLUMNS),
        "feature_names": FEATURE_COLUMNS,
        "n_unique_classes": int(len(unique_classes)),
        "class_counts": {"0": int((y == 0).sum()), "1": int((y == 1).sum())},
        "real_label_source": True,
        "validation_status": "approved_dataset_only",
        "dataset_fingerprint": _dataset_fingerprint(records),
        "regression_target_available": regression_available,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "accuracy": accuracy,
        "rmse": rmse,
        "cv_folds": cv_folds,
        "cv_roc_auc_mean": cv_roc_auc_mean,
        "cv_roc_auc_std": cv_roc_auc_std,
        "cv_f1_mean": cv_f1_mean,
        "cv_f1_std": cv_f1_std,
        "feature_importance": feature_importance,
        "clf_path": clf_path,
        "reg_path": reg_path,
        "scaler_path": scaler_path,
    }
    with open(meta_path, "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)

    with open(os.path.join(MODEL_DIR, "active_model.json"), "w", encoding="utf-8") as handle:
        json.dump({"run_id": run_id, "meta_path": meta_path}, handle, indent=2)

    return meta


def _safe_model_path(path: str) -> bool:
    try:
        return os.path.commonpath([MODEL_DIR, os.path.abspath(path)]) == MODEL_DIR
    except ValueError:
        return False


def load_active_model() -> Optional[Tuple[Any, Any, Any, Dict[str, Any]]]:
    active_path = os.path.join(MODEL_DIR, "active_model.json")
    if not os.path.exists(active_path):
        return None

    try:
        with open(active_path, encoding="utf-8") as handle:
            ref = json.load(handle)
        meta_path = os.path.abspath(str(ref["meta_path"]))
        if not _safe_model_path(meta_path):
            raise ValueError("Invalid model metadata path")

        with open(meta_path, encoding="utf-8") as handle:
            meta = json.load(handle)

        if meta.get("real_label_source") is not True:
            raise ValueError("Model is not marked as trained on approved real data")
        if meta.get("validation_status") != "approved_dataset_only":
            raise ValueError("Model dataset has not passed the approved-data gate")
        if int(meta.get("n_samples", 0)) < MIN_SAMPLES:
            raise ValueError("Model is below the minimum sample threshold")
        if int(meta.get("n_unique_classes", 0)) < 2:
            raise ValueError("Model is single-class")
        if meta.get("feature_names") != FEATURE_COLUMNS:
            raise ValueError("Model feature schema does not match application schema")

        for key in ("clf_path", "scaler_path"):
            if not meta.get(key) or not _safe_model_path(meta[key]):
                raise ValueError(f"Invalid {key}")
        if meta.get("reg_path") and not _safe_model_path(meta["reg_path"]):
            raise ValueError("Invalid regression artifact path")

        with open(meta["clf_path"], "rb") as handle:
            classifier = pickle.load(handle)
        regressor = None
        if meta.get("reg_path"):
            with open(meta["reg_path"], "rb") as handle:
                regressor = pickle.load(handle)
        with open(meta["scaler_path"], "rb") as handle:
            scaler = pickle.load(handle)
        return classifier, regressor, scaler, meta
    except Exception as exc:
        logger.warning("Active model rejected: %s", exc)
        _clear_active_model_files()
        return None
