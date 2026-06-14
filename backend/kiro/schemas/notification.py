from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    content: Optional[str] = None
    notification_type: Optional[str] = None
    related_document_id: Optional[int] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str]
    notification_type: Optional[str]
    is_read: bool
    related_document_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_read: bool = True
