from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ....core.database import get_db
from ....models import AuditLog

router = APIRouter(prefix="/admin/audit-logs", tags=["管理员-审计"])


@router.get("")
def list_audit_logs(
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size
    }
