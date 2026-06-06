from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    category_id: Optional[int] = None
    is_public: bool = True


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class DocumentTemplateResponse(DocumentTemplateBase):
    id: int
    created_by: int
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True