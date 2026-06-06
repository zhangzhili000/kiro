from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ShareResponse(BaseModel):
    id: int
    document_id: int
    share_token: str
    created_by: int
    expires_at: Optional[datetime]
    view_count: int
    created_at: datetime

    class Config:
        from_attributes = True
