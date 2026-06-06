from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from knpy.core.timezone_utils import get_beijing_time
from ..core.database import Base


class ApprovalTemplate(Base):
    __tablename__ = "approval_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    flow_config = Column(JSON, nullable=False)  # 审批流程配置
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("approval_templates.id"))
    current_step = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, approved, rejected, cancelled
    submitted_by = Column(Integer, ForeignKey("users.id"))
    submitted_at = Column(DateTime, default=get_beijing_time)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=get_beijing_time)

    document = relationship("Document")
    template = relationship("ApprovalTemplate")
    submitted_by_user = relationship("User")
    history = relationship("ApprovalHistory", back_populates="approval_record")


class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(Integer, ForeignKey("approval_records.id"), nullable=False)
    step = Column(Integer, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(20), nullable=False)  # approve, reject, transfer
    comment = Column(Text)
    created_at = Column(DateTime, default=get_beijing_time)

    approval_record = relationship("ApprovalRecord", back_populates="history")
    approver = relationship("User")