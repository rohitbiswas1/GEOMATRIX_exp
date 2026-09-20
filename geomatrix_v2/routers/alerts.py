"""Alerts API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, Project
from schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: str = Query("Open"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if status.lower() != "all":
        q = q.filter(Alert.status == status)
    alerts = q.order_by(Alert.detected_at.desc()).limit(limit).all()
    result = []
    for alert in alerts:
        project = db.query(Project).filter_by(id=alert.project_id).first()
        item = AlertOut.model_validate(alert)
        item.project_name = project.name if project else None
        result.append(item)
    return result


@router.get("/summary")
def alerts_summary(db: Session = Depends(get_db)):
    total = db.query(Alert).count()
    open_count = db.query(Alert).filter_by(status="Open").count()
    critical = db.query(Alert).filter_by(severity="Critical", status="Open").count()
    high = db.query(Alert).filter_by(severity="High", status="Open").count()
    return {"total": total, "open": open_count, "critical": critical, "high": high}


@router.patch("/{alert_id}")
def update_alert(alert_id: str, payload: dict, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(404, "Alert not found")
    status = payload.get("status")
    if status not in {"Open", "Acknowledged", "Resolved"}:
        from fastapi import HTTPException
        raise HTTPException(400, "status must be Open, Acknowledged or Resolved")
    alert.status = status
    db.commit()
    db.refresh(alert)
    return {"id": alert.id, "status": alert.status}
