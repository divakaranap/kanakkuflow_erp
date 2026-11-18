from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend.app.models.accounting import AuditLog
from backend.app.models.user import User


def log_audit_event(
    db: Session,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Record an immutable audit log entry for system actions."""
    audit_entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "SYSTEM",
        role=str(user.role.value if hasattr(user, "role") and hasattr(user.role, "value") else (user.role if user else "SYSTEM")),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=details,
        ip_address=ip_address,
        created_at=datetime.now(),
    )
    db.add(audit_entry)
    db.flush()
    return audit_entry
