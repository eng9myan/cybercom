from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_action(
    db: Session,
    *,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    changes: Optional[dict] = None,
    company_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        company_id=company_id if company_id is not None else (user.company_id if user else None),
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
