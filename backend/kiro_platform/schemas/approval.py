from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ApprovalStep(BaseModel):
    step: int
    role: str
    approver_ids: Optional[List[int]] = None


class ApprovalTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    flow_config: dict


class ApprovalTemplateCreate(ApprovalTemplateBase):
    pass


class ApprovalTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    flow_config: Optional[dict] = None
    is_active: Optional[bool] = None


class ApprovalTemplateResponse(ApprovalTemplateBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApprovalRecordCreate(BaseModel):
    document_id: int
    template_id: Optional[int] = None


class ApprovalRecordUpdate(BaseModel):
    status: Optional[str] = None


class ApprovalRecordResponse(BaseModel):
    id: int
    document_id: int
    template_id: Optional[int]
    current_step: int
    status: str
    submitted_by: int
    submitted_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    action: str  # approve, reject
    comment: Optional[str] = None


class ApprovalHistoryResponse(BaseModel):
    id: int
    approval_id: int
    step: int
    approver_id: int
    action: str
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True