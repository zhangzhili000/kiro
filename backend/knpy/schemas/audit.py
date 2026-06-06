from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLogCreate(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str] = None
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
