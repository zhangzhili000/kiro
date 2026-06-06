from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AttachmentResponse(BaseModel):
    id: int
    document_id: int
    filename: str
    original_filename: str
    file_size: Optional[int]
    content_type: Optional[str]
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True