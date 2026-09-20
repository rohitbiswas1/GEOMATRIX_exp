"""ML model status and training endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import HistoricalDelayRecord, ModelRun
from ml.features import REGRESSION_LABEL
from ml.train import InsufficientDataError, train_model
from ml.evaluate import get_model_status

router = APIRouter(prefix="/api/model", tags=["model"])
logger = logging.getLogger(__name__)


@router.get("/status")
def model_status():
    return get_model_status()


@router.get("/training-data")
def get_training_data(db: Session = Depends(get_db)):
    real_records = db.query(HistoricalDelayRecord).filter(
        HistoricalDelayRecord.data_classification.in_([None, "REAL", "real"])
    ).all()
    total = len(real_records)
    delayed = sum(1 for r in real_records if r.delayed is True)
    on_time = sum(1 for r in real_records if r.delayed is False)
    ready = total >= 10 and delayed > 0 and on_time > 0
    message = (
        f"{total} real labeled records available ({delayed} delayed, {on_time} on-time)."
        if total
        else "No real historical records yet. Upload a labeled CSV via Data Ingestion."
    )
    if total >= 10 and (delayed == 0 or on_time == 0):
        message += " Training remains blocked until both delay classes are present."
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
            "is_active": r.is_active,
        }
        for r in runs
    ]


@router.post("/train")
def trigger_training(
    algorithm: str = Query("RandomForest"),
    db: Session = Depends(get_db),
):
    if algorithm not in {"RandomForest", "XGBoost"}:
        raise HTTPException(400, "algorithm must be RandomForest or XGBoost")

    records = db.query(HistoricalDelayRecord).filter(
        HistoricalDelayRecord.data_classification.in_([None, "REAL", "real"])
    ).all()

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
            "actual_delay_days": getattr(r, REGRESSION_LABEL, None),
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
        logger.error("Training failed: %s", exc, exc_info=True)
        raise HTTPException(500, "Training failed. Check server logs for details.") from exc

    db.query(ModelRun).filter_by(is_active=True).update({"is_active": False})
    run = ModelRun(
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
        accuracy=meta.get("accuracy"),
        model_path=meta["clf_path"],
        model_version=meta.get("model_version"),
        notes="Trained on real labeled historical records only.",
        is_active=True,
    )
    db.add(run)
    db.commit()

    return {
        "success": True,
        "message": f"Model trained on {meta['n_samples']} real samples.",
        "model_run_id": meta["run_id"],
        "metrics": {
            "precision": round(meta["precision"], 3),
            "recall": round(meta["recall"], 3),
            "f1_score": round(meta["f1_score"], 3),
            "roc_auc": round(meta["roc_auc"], 3),
            "accuracy": round(meta["accuracy"], 3),
            "rmse": None if meta.get("rmse") is None else round(meta["rmse"], 1),
        },
    }
