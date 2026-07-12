from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = None
    html_content: Optional[str] = None
    category_id: Optional[int] = None
    permission: str = "public"


class DocumentCreate(DocumentBase):
    tag_ids: Optional[List[int]] = []


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    html_content: Optional[str] = None
    category_id: Optional[int] = None
    permission: Optional[str] = None
    tag_ids: Optional[List[int]] = None


class DocumentResponse(DocumentBase):
    id: int
    author_id: int
    author_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    view_count: int
    like_count: int
    comment_count: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    id: int
    title: str
    author_id: Optional[int]
    author_name: Optional[str] = None
    category_id: Optional[int]
    category_name: Optional[str] = None
    permission: str
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionResponse(BaseModel):
    id: int
    document_id: int
    version_number: int
    title: Optional[str]
    content: Optional[str]
    change_summary: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDownloadRequest(BaseModel):
    format: str = "md"


class DocumentIndexStatusResponse(BaseModel):
    document_id: int
    status: str  # pending, processing, completed, failed, cancelled
    progress: int  # 0-100
    message: str
    updated_at: Optional[str] = None
    chunk_count: Optional[int] = None