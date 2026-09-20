import numpy as np
import pytest

import geomatrix_v2.ml.train as train_module
from geomatrix_v2.ml.evaluate import get_model_status
from geomatrix_v2.ml.explain import explain_project
from geomatrix_v2.ml.features import FEATURE_COLUMNS, build_feature_vector, validate_prediction_inputs
from geomatrix_v2.ml.predict import predict_project_risk
from geomatrix_v2.ml.train import InsufficientDataError, train_model


@pytest.fixture(autouse=True)
def isolated_model_artifacts(tmp_path, monkeypatch):
    model_dir = tmp_path / "model_artifacts"
    model_dir.mkdir()
    monkeypatch.setattr(train_module, "MODEL_DIR", str(model_dir))


def _real_record(**overrides):
    record = {
        "land_area_ha": 120.0,
        "affected_families": 150,
        "pending_claims": 14,
        "legal_cases": 5,
        "doc_completeness_pct": 72,
        "approval_pending": True,
        "rr_pending": 8,
        "overdue_milestones": 4,
        "compensation_pending": True,
        "env_clearance_pending": True,
        "actual_delay_days": 45,
        "delayed": True,
        "data_classification": "REAL",
        "validation_status": "validated",
    }
    record.update(overrides)
    return record


def _prediction_record():
    return {
        "land_required": 100,
        "affected_families": 10,
        "current_stage": "In Progress",
        "doc_completeness_pct": 80,
        "objection_count": 2,
        "legal_case_count": 1,
        "rr_status": "Pending",
        "approval_pending": False,
        "overdue_milestones": 1,
        "compensation_status": "Settled",
        "env_clearance_status": "Granted",
        "forest_clearance_status": "Granted",
        "crz_status": "NA",
    }


def test_model_status_reports_no_active_model():
    status = get_model_status()
    assert status["trained"] is False
    assert "no validated model" in status["message"].lower()


def test_predict_project_risk_returns_clear_message_when_model_missing():
    result = predict_project_risk(_prediction_record())
    assert result["status"] == "not_trained"
    assert result["risk_score"] is None
    assert "no validated model" in result["message"].lower()


def test_validate_prediction_inputs_requires_only_core_inputs():
    record = {
        "land_required": 300.0,
        "affected_families": 50,
        "current_stage": "Compensation",
    }
    assert validate_prediction_inputs(record) == []


def test_train_model_rejects_insufficient_real_labeled_data():
    records = [_real_record() for _ in range(9)]
    with pytest.raises(InsufficientDataError, match="Minimum 10"):
        train_model(records)


def test_train_model_rejects_one_class_data():
    records = [_real_record(delayed=True) for _ in range(12)]
    with pytest.raises(InsufficientDataError, match="both delayed and on-time"):
        train_model(records)


def test_training_ignores_non_real_records():
    records = [
        _real_record(delayed=True, data_classification="REAL"),
        _real_record(delayed=False, data_classification="USER_UPLOADED"),
    ]
    with pytest.raises(InsufficientDataError):
        train_model(records)


def test_objection_count_is_preserved():
    record = _prediction_record()
    vector = build_feature_vector(record)
    assert vector["pending_claims"] == 2.0


def test_confidence_never_exceeds_unit_interval(monkeypatch):
    fake_clf = type(
        "FakeClf",
        (),
        {
            "predict_proba": lambda self, X: np.array([[0.9, 0.1]]),
            "classes_": np.array([0, 1]),
        },
    )()
    fake_preprocessor = type("FakePreprocessor", (), {"transform": lambda self, X: X})()
    fake_meta = {
        "used_features": FEATURE_COLUMNS,
        "roc_auc": 1.5,
        "run_id": "r1",
        "model_version": "v1",
        "trained_at": "2026-09-19T00:00:00",
        "n_samples": 10,
        "real_label_source": True,
        "validation_status": "approved_dataset_only",
        "feature_names": FEATURE_COLUMNS,
        "regression_target_available": False,
    }
    monkeypatch.setattr(
        "geomatrix_v2.ml.predict.load_active_model",
        lambda: (fake_clf, None, fake_preprocessor, fake_meta),
    )
    result = predict_project_risk(_prediction_record())
    assert result["status"] == "ok"
    assert 0.0 <= result["confidence"] <= 1.0


def test_missing_regression_target_makes_delay_days_unavailable(monkeypatch):
    fake_clf = type(
        "FakeClf",
        (),
        {
            "predict_proba": lambda self, X: np.array([[0.6, 0.4]]),
            "classes_": np.array([0, 1]),
        },
    )()
    fake_preprocessor = type("FakePreprocessor", (), {"transform": lambda self, X: X})()
    fake_meta = {
        "used_features": FEATURE_COLUMNS,
        "run_id": "r2",
        "model_version": "v2",
        "trained_at": "2026-09-19T00:00:00",
        "n_samples": 10,
        "real_label_source": True,
        "validation_status": "approved_dataset_only",
        "feature_names": FEATURE_COLUMNS,
        "regression_target_available": False,
    }
    monkeypatch.setattr(
        "geomatrix_v2.ml.predict.load_active_model",
        lambda: (fake_clf, None, fake_preprocessor, fake_meta),
    )
    result = predict_project_risk(_prediction_record())
    assert result["status"] == "ok"
    assert result["predicted_delay_days"] is None


def test_shap_unavailable_without_valid_model():
    assert explain_project(_prediction_record()) is None


def test_train_model_writes_reproducible_real_metrics():
    records = [
        _real_record(
            delayed=(i % 2 == 0),
            actual_delay_days=30 + i * 4,
            pending_claims=i % 6,
            legal_cases=i % 4,
            doc_completeness_pct=60 + (i % 30),
            approval_pending=(i % 3 == 0),
            rr_pending=i % 5,
            overdue_milestones=i % 7,
            compensation_pending=(i % 2 == 0),
            env_clearance_pending=(i % 4 == 0),
        )
        for i in range(30)
    ]
    meta = train_model(records)

    assert meta["n_samples"] == 30
    assert meta["n_unique_classes"] == 2
    assert meta["feature_names"] == FEATURE_COLUMNS
    assert meta["model_version"]
    assert meta["dataset_fingerprint"]
    assert 0.0 <= meta["precision"] <= 1.0
    assert 0.0 <= meta["recall"] <= 1.0
    assert 0.0 <= meta["f1_score"] <= 1.0
    assert meta["cv_folds"] >= 2
    assert meta["regression_target_available"] is True


def test_model_artifact_can_be_loaded_after_training(tmp_path):
    records = [
        _real_record(
            delayed=(i % 2 == 0),
            actual_delay_days=10 + i,
            pending_claims=i % 5,
            legal_cases=i % 3,
            doc_completeness_pct=70 + (i % 20),
            approval_pending=(i % 2 == 0),
            rr_pending=i % 4,
            overdue_milestones=i % 3,
            compensation_pending=(i % 2 == 0),
            env_clearance_pending=(i % 3 == 0),
        )
        for i in range(20)
    ]
    train_model(records)
    loaded = train_module.load_active_model()
    assert loaded is not None
    classifier, regressor, preprocessor, meta = loaded
    assert classifier is not None
    assert preprocessor is not None
    assert meta["real_label_source"] is True
