from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryTreeResponse(CategoryResponse):
    children: List["CategoryTreeResponse"] = []

    class Config:
        from_attributes = True


CategoryTreeResponse.model_rebuild()
