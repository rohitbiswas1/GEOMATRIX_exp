"""Model status, offline-training controls, and model audit endpoints."""
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..database import get_db
from ..models import HistoricalDelayRecord, ModelRun
from ..ml.train import InsufficientDataError, train_model
from ..ml.evaluate import get_model_status

router = APIRouter(prefix="/api/model", tags=["model"])
logger = logging.getLogger(__name__)


def _require_runtime_training_enabled() -> None:
    if os.getenv("APP_ENV", "development").lower() == "production" and os.getenv("ALLOW_RUNTIME_TRAINING", "false").strip().lower() != "true":
        raise HTTPException(
            403,
            "Runtime model training is disabled. Train and validate the approved model offline, then deploy the model artifact.",
        )


@router.get("/status")
def model_status():
    return get_model_status()


@router.get("/training-data")
def get_training_data(db: Session = Depends(get_db)):
    records = (
        db.query(HistoricalDelayRecord)
        .filter(HistoricalDelayRecord.data_classification == "REAL", HistoricalDelayRecord.validation_status.in_([None, "validated", "approved"]))
        .all()
    )
    total = len(records)
    delayed = sum(1 for r in records if r.delayed is True)
    on_time = sum(1 for r in records if r.delayed is False)
    ready = total >= 10 and delayed > 0 and on_time > 0
    message = (
        f"{total} real labeled records available ({delayed} delayed, {on_time} on-time)."
        if total else
        "No approved real historical records available."
    )
    if total and not ready:
        message += " Both delay classes and at least 10 total real labels are required."
    return {
        "total_records": total,
        "delayed_count": delayed,
        "on_time_count": on_time,
        "ready_to_train": ready,
        "message": message,
    }


@router.get("/runs")
def list_model_runs(db: Session = Depends(get_db)):
    runs = db.query(ModelRun).order_by(ModelRun.trained_at.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "algorithm": r.algorithm,
            "trained_at": r.trained_at.isoformat() if r.trained_at else None,
            "n_samples": r.n_samples,
            "precision": r.precision,
            "recall": r.recall,
            "f1_score": r.f1_score,
            "roc_auc": r.roc_auc,
            "rmse": r.rmse,
            "accuracy": r.accuracy,
            "is_active": r.is_active,
            "model_version": r.model_version,
            "notes": r.notes,
        }
        for r in runs
    ]


@router.post("/train")
def trigger_training(
    request: Request,
    algorithm: str = Query("RandomForest"),
    db: Session = Depends(get_db),
):
    _require_runtime_training_enabled()
    if algorithm not in {"RandomForest", "XGBoost"}:
        raise HTTPException(400, "algorithm must be RandomForest or XGBoost")

    records = (
        db.query(HistoricalDelayRecord)
        .filter(HistoricalDelayRecord.data_classification == "REAL", HistoricalDelayRecord.validation_status.in_([None, "validated", "approved"]))
        .all()
    )
    record_dicts = [
        {
            "land_area_ha": r.land_area_ha,
            "affected_families": r.affected_families,
            "pending_claims": r.pending_claims,
            "legal_cases": r.legal_cases,
            "doc_completeness_pct": r.doc_completeness_pct,
            "approval_pending": r.approval_pending,
            "rr_pending": r.rr_pending,
            "overdue_milestones": r.overdue_milestones,
            "actual_delay_days": r.actual_delay_days,
            "delayed": r.delayed,
            "data_classification": r.data_classification,
        }
        for r in records
    ]
    try:
        meta = train_model(record_dicts, algorithm=algorithm)
    except InsufficientDataError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.error("Training failed", exc_info=True)
        raise HTTPException(500, "Training failed. Check server logs for details.") from exc

    db.query(ModelRun).filter_by(is_active=True).update({"is_active": False})
    db.add(
        ModelRun(
            id=meta["run_id"],
            algorithm=meta["algorithm"],
            n_samples=meta["n_samples"],
            n_features=meta["n_features"],
            feature_names=meta["feature_names"],
            precision=meta["precision"],
            recall=meta["recall"],
            f1_score=meta["f1_score"],
            roc_auc=meta["roc_auc"],
            rmse=meta["rmse"],
            accuracy=meta["accuracy"],
            model_path=os.path.basename(meta["clf_path"]),
            model_version=meta["model_version"],
            notes="Validated on explicitly approved real historical records.",
            is_active=True,
        )
    )
    write_audit(
        db,
        actor_email=getattr(request.state, "user", {}).get("email") if request is not None and getattr(request.state, "user", None) else None,
        action="TRAIN_MODEL",
        entity_type="MODEL",
        entity_id=meta["run_id"],
        new_value={"algorithm": meta["algorithm"], "n_samples": meta["n_samples"], "dataset_fingerprint": meta["dataset_fingerprint"]},
        request_id=getattr(request.state, "request_id", None) if request is not None else None,
    )
    db.commit()
    return {
        "success": True,
        "message": f"Model trained on {meta['n_samples']} approved real samples.",
        "model_run_id": meta["run_id"],
        "metrics": {
            "precision": round(meta["precision"], 3),
            "recall": round(meta["recall"], 3),
            "f1_score": round(meta["f1_score"], 3),
            "roc_auc": None if meta.get("roc_auc") is None else round(meta["roc_auc"], 3),
            "accuracy": round(meta["accuracy"], 3),
            "rmse": None if meta.get("rmse") is None else round(meta["rmse"], 1),
        },
    }
