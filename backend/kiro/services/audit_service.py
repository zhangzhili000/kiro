from datetime import datetime
from typing import List, Optional

from kiro.core.database import SessionLocal
from kiro.models.notification import AuditLog
from kiro.schemas.audit import AuditLogCreate, AuditLogResponse


def create_audit_log(db, audit_log_create: AuditLogCreate) -> AuditLog:
    audit_log = AuditLog(
        user_id=audit_log_create.user_id,
        user_name=audit_log_create.user_name,
        action=audit_log_create.action,
        resource_type=audit_log_create.resource_type,
        resource_id=audit_log_create.resource_id,
        details=audit_log_create.details,
        ip_address=audit_log_create.ip_address
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(db, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[AuditLog]:
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


def get_audit_log_response(audit_log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=audit_log.id,
        user_id=audit_log.user_id,
        user_name=audit_log.user_name,
        action=audit_log.action,
        resource_type=audit_log.resource_type,
        resource_id=audit_log.resource_id,
        details=audit_log.details,
        ip_address=audit_log.ip_address,
        created_at=audit_log.created_at
    )


def log_action(db, user_id: int, user_name: str, action: str, resource_type: str, resource_id: Optional[int] = None, details: Optional[str] = None, ip_address: Optional[str] = None):
    audit_log = AuditLog(
        user_id=user_id,
        user_name=user_name,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
