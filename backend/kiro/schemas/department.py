from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DepartmentBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentTreeResponse(DepartmentResponse):
    children: List["DepartmentTreeResponse"] = []

    class Config:
        from_attributes = True


DepartmentTreeResponse.model_rebuild()
