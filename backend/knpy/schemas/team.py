from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamDocumentResponse(BaseModel):
    id: int
    team_id: int
    document_id: int
    added_by: int
    added_at: datetime

    class Config:
        from_attributes = True