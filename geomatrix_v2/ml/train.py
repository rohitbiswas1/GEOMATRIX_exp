"""Reproducible GEOMATRIX model training.

Training is permitted only from records marked REAL and validated/approved.
Missing source values are handled by an explicit training-time imputation
pipeline; they are never silently replaced by hard-coded business values.
"""
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
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from .features import FEATURE_COLUMNS, LABEL_COLUMN, REGRESSION_LABEL

logger = logging.getLogger(__name__)

MIN_SAMPLES = 10
MIN_FEATURES = 5
MIN_REGRESSION_SAMPLES = 20
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model_artifacts"))
os.makedirs(MODEL_DIR, exist_ok=True)

class InsufficientDataError(Exception):
    pass

def _clear_active_model_files() -> None:
    active = os.path.join(MODEL_DIR, "active_model.json")
    try:
        if os.path.exists(active):
            os.remove(active)
    except OSError:
        logger.warning("Unable to remove active model pointer")

def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record for record in records
        if isinstance(record, dict)
        and record.get(LABEL_COLUMN) is not None
        and str(record.get("data_classification") or "REAL").strip().upper() == "REAL"
        and str(record.get("validation_status") or "validated").strip().lower() in {"validated", "approved"}
    ]

def _dataset_fingerprint(records: list[dict[str, Any]]) -> str:
    selected = [
        {key: record.get(key) for key in sorted(FEATURE_COLUMNS + [LABEL_COLUMN, REGRESSION_LABEL])}
        for record in records
    ]
    canonical = json.dumps(selected, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _classifier(algorithm: str):
    if algorithm == "XGBoost" and XGBOOST_AVAILABLE:
        return XGBClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, random_state=42,
            eval_metric="logloss", verbosity=0,
        )
    return RandomForestClassifier(
        n_estimators=250, max_depth=8, min_samples_leaf=2,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )

def _regressor(algorithm: str):
    if algorithm == "XGBoost" and XGBOOST_AVAILABLE:
        return XGBRegressor(
            n_estimators=150, max_depth=4, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, random_state=42,
            objective="reg:squarederror", verbosity=0,
        )
    return RandomForestRegressor(
        n_estimators=250, max_depth=8, min_samples_leaf=2,
        random_state=42, n_jobs=-1,
    )

def _preprocessor() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", StandardScaler()),
    ])

def train_model(records: list[dict[str, Any]], algorithm: str = "RandomForest") -> Dict[str, Any]:
    records = _normalize_records(records)
    if len(records) < MIN_SAMPLES:
        raise InsufficientDataError(f"Only {len(records)} approved real labeled records are available. Minimum {MIN_SAMPLES} is required.")

    from .features import build_feature_dataframe
    try:
        frame = build_feature_dataframe(records)
    except ValueError as exc:
        raise InsufficientDataError(str(exc)) from exc

    y = np.asarray([bool(record[LABEL_COLUMN]) for record in records], dtype=int)
    if len(np.unique(y)) < 2:
        raise InsufficientDataError("Training rejected: both delayed and on-time real labels are required.")

    used_features = [feature for feature in FEATURE_COLUMNS if frame[feature].notna().any()]
    if len(used_features) < MIN_FEATURES:
        raise InsufficientDataError(
            f"Only {len(used_features)} model features contain source data. At least {MIN_FEATURES} usable features are required."
        )

    algorithm = algorithm if algorithm in {"RandomForest", "XGBoost"} else "RandomForest"
    classifier = _classifier(algorithm)

    X = frame[used_features]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    preprocessor = _preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    classifier.fit(X_train_t, y_train)

    classes = list(getattr(classifier, "classes_", []))
    if 1 not in classes:
        raise InsufficientDataError("Trained classifier does not contain the delay class.")
    delay_idx = classes.index(1)

    y_pred = classifier.predict(X_test_t)
    y_prob = classifier.predict_proba(X_test_t)[:, delay_idx]

    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else None

    cv_folds = min(5, int(np.bincount(y).min()))
    cv_roc_auc_mean = cv_roc_auc_std = cv_f1_mean = cv_f1_std = None
    if cv_folds >= 2:
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        try:
            pipeline = Pipeline([
                ("preprocess", _preprocessor()),
                ("classifier", _classifier(algorithm)),
            ])
            cv_auc = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
            cv_f1 = cross_val_score(pipeline, X, y, cv=cv, scoring="f1")
            cv_roc_auc_mean = float(cv_auc.mean())
            cv_roc_auc_std = float(cv_auc.std())
            cv_f1_mean = float(cv_f1.mean())
            cv_f1_std = float(cv_f1.std())
        except Exception:
            logger.exception("Cross-validation failed")

    regression_available = (
        len(records) >= MIN_REGRESSION_SAMPLES
        and all(record.get(REGRESSION_LABEL) not in (None, "") for record in records)
    )
    regressor = None
    rmse = None
    if regression_available:
        regressor = _regressor(algorithm)
        # Use the same deterministic split used for the classifier.
        train_indices, test_indices = train_test_split(
            np.arange(len(records)), test_size=0.2, random_state=42, stratify=y,
        )
        regressor.fit(
            preprocessor.transform(frame.iloc[train_indices][used_features]),
            np.asarray([float(records[i][REGRESSION_LABEL]) for i in train_indices]),
        )
        reg_pred = regressor.predict(preprocessor.transform(frame.iloc[test_indices][used_features]))
        rmse = float(np.sqrt(mean_squared_error(
            np.asarray([float(records[i][REGRESSION_LABEL]) for i in test_indices]),
            reg_pred,
        )))

    feature_importance = {
        feature: round(float(value), 6)
        for feature, value in zip(used_features, classifier.feature_importances_[:len(used_features)])
    }

    run_id = str(uuid.uuid4())
    version = f"{algorithm.lower()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    clf_path = os.path.join(MODEL_DIR, f"clf_{run_id}.pkl")
    reg_path = os.path.join(MODEL_DIR, f"reg_{run_id}.pkl") if regressor is not None else None
    preprocessor_path = os.path.join(MODEL_DIR, f"preprocessor_{run_id}.pkl")
    meta_path = os.path.join(MODEL_DIR, f"meta_{run_id}.json")

    with open(clf_path, "wb") as handle:
        pickle.dump(classifier, handle)
    if regressor is not None and reg_path:
        with open(reg_path, "wb") as handle:
            pickle.dump(regressor, handle)
    with open(preprocessor_path, "wb") as handle:
        pickle.dump(preprocessor, handle)

    meta = {
        "run_id": run_id,
        "model_version": version,
        "algorithm": algorithm,
        "trained_at": datetime.utcnow().isoformat(),
        "n_samples": len(records),
        "n_features": len(used_features),
        "feature_names": FEATURE_COLUMNS,
        "used_features": used_features,
        "n_unique_classes": int(len(np.unique(y))),
        "class_counts": {"0": int((y == 0).sum()), "1": int((y == 1).sum())},
        "real_label_source": True,
        "validation_status": "approved_dataset_only",
        "dataset_fingerprint": _dataset_fingerprint(records),
        "imputation_strategy": "median",
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
        "preprocessor_path": preprocessor_path,
    }
    with open(meta_path, "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)

    with open(os.path.join(MODEL_DIR, "active_model.json"), "w", encoding="utf-8") as handle:
        json.dump({"run_id": run_id, "meta_path": meta_path}, handle, indent=2)

    return meta

def _safe_path(path: str) -> bool:
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
        if not _safe_path(meta_path):
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
        if meta.get("used_features") is None or len(meta["used_features"]) < MIN_FEATURES:
            raise ValueError("Model does not have enough validated features")
        if meta.get("feature_names") != FEATURE_COLUMNS:
            raise ValueError("Model feature schema does not match application schema")
        for key in ("clf_path", "preprocessor_path"):
            if not meta.get(key) or not _safe_path(meta[key]):
                raise ValueError(f"Invalid {key}")
        if meta.get("reg_path") and not _safe_path(meta["reg_path"]):
            raise ValueError("Invalid regression artifact path")

        with open(meta["clf_path"], "rb") as handle:
            classifier = pickle.load(handle)
        regressor = None
        if meta.get("reg_path"):
            with open(meta["reg_path"], "rb") as handle:
                regressor = pickle.load(handle)
        with open(meta["preprocessor_path"], "rb") as handle:
            preprocessor = pickle.load(handle)
        return classifier, regressor, preprocessor, meta
    except Exception as exc:
        logger.warning("Active model rejected: %s", exc)
        _clear_active_model_files()
        return None
