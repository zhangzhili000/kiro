from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from knpy.core.timezone_utils import get_beijing_time
from ..core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    notification_type = Column(String(50))
    is_read = Column(Boolean, default=False)
    related_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=get_beijing_time)

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=get_beijing_time)

    user = relationship("User", back_populates="audit_logs")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword = Column(String(200), nullable=False)
    search_type = Column(String(20), default="fulltext")
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time)

    user = relationship("User", back_populates="search_history")
