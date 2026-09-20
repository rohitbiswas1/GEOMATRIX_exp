"""Project CRUD, validation, prediction and prediction history."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..database import get_db
from ..models import Alert, Project, RiskPrediction
from ..schemas import DashboardSummary, ProjectCreate, ProjectOut, ProjectUpdate, ProjectValidation
from ..ml.explain import explain_project
from ..ml.features import validate_prediction_inputs
from ..ml.predict import predict_project_risk

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_to_record(project: Project) -> dict:
    return {
        "land_area_ha": project.land_required,
        "land_required": project.land_required,
        "affected_families": project.affected_families,
        "pending_claims": project.objection_count,
        "objection_count": project.objection_count,
        "legal_cases": project.legal_case_count,
        "legal_case_count": project.legal_case_count,
        "doc_completeness_pct": project.doc_completeness_pct,
        "approval_pending": project.approval_pending,
        "rr_pending": project.rr_status,
        "rr_status": project.rr_status,
        "overdue_milestones": project.overdue_milestones,
        "compensation_status": project.compensation_status,
        "compensation_pending": project.compensation_status,
        "env_clearance_status": project.env_clearance_status,
        "forest_clearance_status": project.forest_clearance_status,
        "crz_status": project.crz_status,
        "current_stage": project.current_stage,
    }


@router.get("/dashboard-summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    scored = [p.risk_score for p in projects if p.risk_score is not None]
    total = len(projects)
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
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(Project).filter_by(project_code=body.project_code).first()
    if existing:
        raise HTTPException(409, f"Project code '{body.project_code}' already exists")
    data = body.model_dump(exclude_none=False)
    data["data_classification"] = "USER_ENTERED"
    data["validation_status"] = "pending"
    data.pop("source_url", None)
    data.pop("source_record_id", None)
    project = Project(
        id=str(uuid.uuid4()),
        imported_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **data,
    )
    db.add(project)
    write_audit(
        db,
        actor_email=getattr(request.state, "user", {}).get("email") if getattr(request.state, "user", None) else None,
        action="CREATE",
        entity_type="PROJECT",
        entity_id=project.id,
        new_value={"project_code": project.project_code, "name": project.name, "data_classification": project.data_classification},
        request_id=getattr(request.state, "request_id", None),
    )
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, body: ProjectUpdate, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    update_data = body.model_dump(exclude_none=True)
    previous = {field: getattr(project, field) for field in update_data}
    model_input_fields = {
        "land_required", "affected_families", "current_stage", "doc_completeness_pct",
        "objection_count", "legal_case_count", "rr_status", "approval_pending",
        "overdue_milestones", "compensation_status", "env_clearance_status",
        "forest_clearance_status", "crz_status", "overdue_milestones",
    }
    for field, value in update_data.items():
        setattr(project, field, value)
    if model_input_fields.intersection(update_data):
        project.risk_score = None
        project.risk_level = None
        project.delay_probability = None
        project.predicted_delay_days = None
        project.confidence = None
        project.primary_driver = None
        project.validation_status = "pending"
    project.updated_at = datetime.utcnow()

    write_audit(
        db,
        actor_email=getattr(request.state, "user", {}).get("email") if getattr(request.state, "user", None) else None,
        action="UPDATE",
        entity_type="PROJECT",
        entity_id=project.id,
        previous_value=previous,
        new_value=update_data,
        request_id=getattr(request.state, "request_id", None),
    )
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    write_audit(
        db,
        actor_email=getattr(request.state, "user", {}).get("email") if getattr(request.state, "user", None) else None,
        action="DELETE",
        entity_type="PROJECT",
        entity_id=project.id,
        previous_value={"project_code": project.project_code, "name": project.name},
        request_id=getattr(request.state, "request_id", None),
    )
    db.delete(project)
    db.commit()


@router.get("/{project_id}/validate", response_model=ProjectValidation)
def validate_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    missing = validate_prediction_inputs(_project_to_record(project))
    return ProjectValidation(
        project_id=project_id,
        missing_fields=missing,
        can_predict=not missing,
        message=(
            "All model inputs present — prediction can proceed."
            if not missing
            else f"Prediction unavailable — missing: {', '.join(missing)}."
        ),
    )


@router.post("/{project_id}/predict-risk")
def predict_risk(project_id: str, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    record = _project_to_record(project)
    missing = validate_prediction_inputs(record)
    if missing:
        raise HTTPException(422, f"Prediction unavailable — missing: {', '.join(missing)}")

    result = predict_project_risk(record)
    if not result or result.get("status") == "not_trained":
        raise HTTPException(503, "No validated model is deployed.")
    if result.get("status") == "error":
        raise HTTPException(500, result.get("message", "Prediction failed"))

    shap_features = explain_project(record) or []
    project.risk_score = result["risk_score"]
    project.risk_level = result["risk_level"]
    project.delay_probability = result["delay_probability"]
    project.predicted_delay_days = result["predicted_delay_days"]
    project.confidence = result["confidence"]
    project.primary_driver = shap_features[0]["feature"] if shap_features else None
    project.updated_at = datetime.utcnow()

    db.add(
        RiskPrediction(
            id=str(uuid.uuid4()),
            project_id=project.id,
            model_run_id=result.get("model_run_id"),
            risk_score=result.get("risk_score"),
            risk_level=result.get("risk_level"),
            delay_probability=result.get("delay_probability"),
            predicted_delay_days=result.get("predicted_delay_days"),
            confidence=result.get("confidence"),
            shap_values={item["feature"]: item["shap_value"] for item in shap_features},
        )
    )
    write_audit(
        db,
        actor_email=getattr(request.state, "user", {}).get("email") if getattr(request.state, "user", None) else None,
        action="PREDICT_RISK",
        entity_type="PROJECT",
        entity_id=project.id,
        new_value={"model_run_id": result.get("model_run_id"), "risk_score": result.get("risk_score"), "risk_level": result.get("risk_level")},
        request_id=getattr(request.state, "request_id", None),
    )
    db.commit()
    return {"project_id": project_id, "prediction": {**result, "shap_features": shap_features}}


@router.get("/{project_id}/explain")
def get_explanation(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    shap_features = explain_project(_project_to_record(project))
    if shap_features is None:
        raise HTTPException(503, "No validated model is deployed.")
    return {"project_id": project_id, "shap_features": shap_features}


@router.get("/{project_id}/predictions")
def list_predictions(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
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
            "id": p.id,
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "delay_probability": p.delay_probability,
            "confidence": p.confidence,
            "predicted_delay_days": p.predicted_delay_days,
            "predicted_at": p.predicted_at.isoformat() if p.predicted_at else None,
            "model_run_id": p.model_run_id,
        }
        for p in preds
    ]
