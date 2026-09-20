"""Project CRUD, validation and ML prediction endpoints."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Project, RiskPrediction, Alert
from schemas import ProjectOut, ProjectCreate, ProjectUpdate, ProjectValidation, DashboardSummary
from ml.predict import predict_project_risk
from ml.explain import explain_project
from ml.features import validate_prediction_inputs

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_to_record(p: Project) -> dict:
    return {
        "land_area_ha": p.land_required,
        "land_required": p.land_required,
        "affected_families": p.affected_families,
        "pending_claims": p.objection_count,
        "objection_count": p.objection_count,
        "legal_cases": p.legal_case_count,
        "legal_case_count": p.legal_case_count,
        "doc_completeness_pct": p.doc_completeness_pct,
        "approval_pending": p.approval_pending,
        "rr_pending": p.rr_status,
        "rr_status": p.rr_status,
        "overdue_milestones": p.overdue_milestones,
        "compensation_status": p.compensation_status,
        "compensation_pending": p.compensation_status,
        "env_clearance_status": p.env_clearance_status,
        "forest_clearance_status": p.forest_clearance_status,
        "crz_status": p.crz_status,
        "current_stage": p.current_stage,
    }


@router.get("/dashboard-summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    total = db.query(Project).count()
    projects = db.query(Project).all()
    scored = [p.risk_score for p in projects if p.risk_score is not None]
    return DashboardSummary(
        total_projects=total,
        critical_count=db.query(Project).filter(Project.risk_level == "Critical").count(),
        high_count=db.query(Project).filter(Project.risk_level == "High").count(),
        medium_count=db.query(Project).filter(Project.risk_level == "Medium").count(),
        low_count=db.query(Project).filter(Project.risk_level == "Low").count(),
        total_land_ha=round(sum(p.land_required or 0 for p in projects), 1),
        total_families=sum(p.affected_families or 0 for p in projects),
        avg_risk_score=round(sum(scored) / len(scored), 1) if scored else None,
        alerts_open=db.query(Alert).filter(Alert.status == "Open").count(),
        data_available=total > 0,
        message=f"{total} projects loaded from database." if total else "No projects in database yet.",
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Project)
    if state:
        q = q.filter(Project.state.ilike(f"%{state}%"))
    if district:
        q = q.filter(Project.district.ilike(f"%{district}%"))
    if stage:
        q = q.filter(Project.current_stage.ilike(f"%{stage}%"))
    if risk_level:
        q = q.filter(Project.risk_level == risk_level)
    return q.order_by(Project.updated_at.desc()).limit(limit).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Project).filter_by(project_code=body.project_code).first()
    if existing:
        raise HTTPException(409, f"Project code '{body.project_code}' already exists")
    project_data = body.model_dump(exclude_none=False)
    # User-created projects are entered for analysis. They are not historical
    # training records, and are not stamped as REAL unless backed by a source.
    project_data["data_classification"] = "USER_ENTERED"
    project_data["validation_status"] = "pending"
    project_data.pop("source_url", None)
    project_data.pop("source_record_id", None)
    proj = Project(
        id=str(uuid.uuid4()),
        imported_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **project_data,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, body: ProjectUpdate, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    db.delete(p)
    db.commit()


@router.get("/{project_id}/validate", response_model=ProjectValidation)
def validate_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    record = _project_to_record(p)
    missing = validate_prediction_inputs(record)
    return ProjectValidation(
        project_id=project_id,
        missing_fields=missing,
        can_predict=not missing,
        message=(
            "All required fields present — prediction can proceed."
            if not missing
            else f"Prediction unavailable: missing {', '.join(missing)}."
        ),
    )


@router.post("/{project_id}/predict-risk")
def predict_risk(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")

    missing = validate_prediction_inputs(_project_to_record(p))
    if missing:
        raise HTTPException(422, f"Prediction unavailable — missing: {', '.join(missing)}")

    result = predict_project_risk(_project_to_record(p))
    if not result or result.get("status") == "not_trained":
        raise HTTPException(503, "Model not trained — insufficient valid real labeled data.")
    if result.get("status") == "error":
        raise HTTPException(500, result.get("message", "Prediction failed"))

    shap_features = explain_project(_project_to_record(p)) or []

    p.risk_score = result.get("risk_score")
    p.risk_level = result.get("risk_level")
    p.delay_probability = result.get("delay_probability")
    p.predicted_delay_days = result.get("predicted_delay_days")
    p.confidence = result.get("confidence")
    p.primary_driver = result.get("model_version")
    p.updated_at = datetime.utcnow()

    db.add(RiskPrediction(
        id=str(uuid.uuid4()),
        project_id=p.id,
        model_run_id=result.get("model_run_id"),
        risk_score=result.get("risk_score"),
        risk_level=result.get("risk_level"),
        delay_probability=result.get("delay_probability"),
        predicted_delay_days=result.get("predicted_delay_days"),
        confidence=result.get("confidence"),
        shap_values={item["feature"]: item["shap_value"] for item in shap_features},
    ))
    db.commit()

    return {"project_id": project_id, "prediction": {**result, "shap_features": shap_features}}


@router.get("/{project_id}/explain")
def get_explanation(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    shap_features = explain_project(_project_to_record(p))
    if shap_features is None:
        raise HTTPException(503, "ML model not trained. Cannot compute SHAP explanations.")
    return {"project_id": project_id, "shap_features": shap_features}


@router.get("/{project_id}/predictions")
def list_predictions(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    preds = (
        db.query(RiskPrediction)
        .filter_by(project_id=project_id)
        .order_by(RiskPrediction.predicted_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": pr.id,
            "risk_score": pr.risk_score,
            "risk_level": pr.risk_level,
            "delay_probability": pr.delay_probability,
            "confidence": pr.confidence,
            "predicted_delay_days": pr.predicted_delay_days,
            "predicted_at": pr.predicted_at.isoformat() if pr.predicted_at else None,
            "model_run_id": pr.model_run_id,
        }
        for pr in preds
    ]
