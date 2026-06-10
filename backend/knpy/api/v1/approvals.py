from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from kiro.core.database import get_db
from kiro.api.v1.users import get_current_user
from kiro.models.user import User
from kiro.schemas.approval import (
    ApprovalTemplateCreate, ApprovalTemplateUpdate, ApprovalTemplateResponse,
    ApprovalRecordCreate, ApprovalRecordResponse, ApprovalAction, ApprovalHistoryResponse
)
from kiro.services.approval_service import (
    get_templates, get_template, create_template, update_template, delete_template,
    submit_for_approval, get_pending_approvals, approve_document, reject_document,
    get_approval_history
)

router = APIRouter(prefix="/approvals", tags=["审批流程"])


@router.get("/templates", response_model=List[ApprovalTemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审批模板列表"""
    return get_templates(db)


@router.get("/templates/{template_id}", response_model=ApprovalTemplateResponse)
def get_template_detail(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审批模板详情"""
    template = get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="审批模板不存在")
    return template


@router.post("/templates", response_model=ApprovalTemplateResponse)
def create_approval_template(
    template: ApprovalTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建审批模板"""
    return create_template(db, template, current_user.id)


@router.put("/templates/{template_id}", response_model=ApprovalTemplateResponse)
def update_approval_template(
    template_id: int,
    template_update: ApprovalTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新审批模板"""
    template = update_template(db, template_id, template_update)
    if not template:
        raise HTTPException(status_code=404, detail="审批模板不存在")
    return template


@router.delete("/templates/{template_id}")
def delete_approval_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除审批模板"""
    success = delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="审批模板不存在")
    return {"message": "审批模板已删除"}


@router.post("/submit", response_model=ApprovalRecordResponse)
def submit_document_for_approval(
    document_id: int,
    template_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交文档审批"""
    try:
        return submit_for_approval(db, document_id, current_user.id, template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/pending", response_model=List[ApprovalRecordResponse])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待审批列表"""
    return get_pending_approvals(db, current_user.id)


@router.post("/{approval_id}/approve", response_model=ApprovalRecordResponse)
def approve_doc(
    approval_id: int,
    action: ApprovalAction = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审批通过"""
    try:
        return approve_document(db, approval_id, current_user.id, action.comment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{approval_id}/reject", response_model=ApprovalRecordResponse)
def reject_doc(
    approval_id: int,
    action: ApprovalAction = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝审批"""
    try:
        return reject_document(db, approval_id, current_user.id, action.comment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{approval_id}/history", response_model=List[ApprovalHistoryResponse])
def get_history(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审批历史"""
    return get_approval_history(db, approval_id)