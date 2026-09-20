"""Minimal audit-log helper."""
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from .models import AuditLog

def write_audit(db: Session, *, actor_email: str | None, action: str, entity_type: str, entity_id: str, previous_value: dict[str, Any] | None = None, new_value: dict[str, Any] | None = None, request_id: str | None = None) -> None:
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_value=previous_value,
        new_value=new_value,
        request_id=request_id,
        timestamp=datetime.utcnow(),
    ))
