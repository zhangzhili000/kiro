from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from kiro.core.timezone_utils import get_beijing_time

from kiro.models.approval import ApprovalTemplate, ApprovalRecord, ApprovalHistory
from kiro.models.document import Document
from kiro.schemas.approval import ApprovalTemplateCreate, ApprovalTemplateUpdate, ApprovalRecordCreate


def get_templates(db: Session) -> List[ApprovalTemplate]:
    return db.query(ApprovalTemplate).filter(ApprovalTemplate.is_active == True).all()


def get_template(db: Session, template_id: int) -> Optional[ApprovalTemplate]:
    return db.query(ApprovalTemplate).filter(
        ApprovalTemplate.id == template_id,
        ApprovalTemplate.is_active == True
    ).first()


def create_template(db: Session, template: ApprovalTemplateCreate, user_id: int) -> ApprovalTemplate:
    db_template = ApprovalTemplate(
        name=template.name,
        description=template.description,
        flow_config=template.flow_config
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def update_template(db: Session, template_id: int, template_update: ApprovalTemplateUpdate) -> Optional[ApprovalTemplate]:
    db_template = get_template(db, template_id)
    if not db_template:
        return None
    
    update_data = template_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int) -> bool:
    db_template = get_template(db, template_id)
    if not db_template:
        return False
    
    db_template.is_active = False
    db.commit()
    return True


def submit_for_approval(db: Session, document_id: int, user_id: int, template_id: Optional[int] = None) -> ApprovalRecord:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError("文档不存在")
    
    db_record = ApprovalRecord(
        document_id=document_id,
        template_id=template_id,
        current_step=0,
        status="pending",
        submitted_by=user_id
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # 更新文档状态为待审核
    document.status = "pending_review"
    db.commit()
    
    return db_record


def get_pending_approvals(db: Session, user_id: int) -> List[ApprovalRecord]:
    """获取用户待审批的文档"""
    from kiro.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # 根据用户角色获取待审批记录
    # 简化实现：返回所有待审批记录
    return db.query(ApprovalRecord).filter(ApprovalRecord.status == "pending").all()


def approve_document(db: Session, approval_id: int, user_id: int, comment: Optional[str] = None) -> ApprovalRecord:
    approval = db.query(ApprovalRecord).filter(ApprovalRecord.id == approval_id).first()
    if not approval:
        raise ValueError("审批记录不存在")
    
    # 创建审批历史记录
    history = ApprovalHistory(
        approval_id=approval_id,
        step=approval.current_step,
        approver_id=user_id,
        action="approve",
        comment=comment
    )
    db.add(history)
    
    # 检查是否还有后续审批步骤
    if approval.template_id:
        template = get_template(db, approval.template_id)
        if template:
            steps = template.flow_config.get("steps", [])
            if approval.current_step + 1 < len(steps):
                approval.current_step += 1
            else:
                approval.status = "approved"
                approval.approved_at = get_beijing_time()
                # 更新文档状态为已发布
                document = db.query(Document).filter(Document.id == approval.document_id).first()
                if document:
                    document.status = "published"
    else:
        # 无模板，直接通过
        approval.status = "approved"
        approval.approved_at = get_beijing_time()
        document = db.query(Document).filter(Document.id == approval.document_id).first()
        if document:
            document.status = "published"
    
    db.commit()
    db.refresh(approval)
    return approval


def reject_document(db: Session, approval_id: int, user_id: int, comment: Optional[str] = None) -> ApprovalRecord:
    approval = db.query(ApprovalRecord).filter(ApprovalRecord.id == approval_id).first()
    if not approval:
        raise ValueError("审批记录不存在")
    
    # 创建审批历史记录
    history = ApprovalHistory(
        approval_id=approval_id,
        step=approval.current_step,
        approver_id=user_id,
        action="reject",
        comment=comment
    )
    db.add(history)
    
    approval.status = "rejected"
    approval.approved_at = get_beijing_time()
    
    # 更新文档状态为被拒绝
    document = db.query(Document).filter(Document.id == approval.document_id).first()
    if document:
        document.status = "rejected"
    
    db.commit()
    db.refresh(approval)
    return approval


def get_approval_history(db: Session, approval_id: int) -> List[ApprovalHistory]:
    return db.query(ApprovalHistory).filter(
        ApprovalHistory.approval_id == approval_id
    ).order_by(ApprovalHistory.created_at.desc()).all()