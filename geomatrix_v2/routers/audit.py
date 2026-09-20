"""Read-only audit log endpoint."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("")
def audit_log(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": row.id,
            "actor_email": row.actor_email,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "previous_value": row.previous_value,
            "new_value": row.new_value,
            "request_id": row.request_id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        }
        for row in rows
    ]
