from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CommentBase(BaseModel):
    content: str
    document_id: int
    parent_id: Optional[int] = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    document_id: int
    user_id: int
    parent_id: Optional[int]
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True