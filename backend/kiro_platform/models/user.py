from sqlalchemy import Column, String, DateTime, Boolean, Text, Table, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.timezone_utils import get_beijing_time
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255))
    name = Column(String(100))
    full_name = Column(String(100))
    avatar = Column(String(500))
    phone = Column(String(20))
    role = Column(String(20), default="user")
    sso_provider = Column(String(50))  # dingtalk, wechatwork, feishu
    sso_id = Column(String(255))  # SSO平台用户ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    documents = relationship("Document", back_populates="author", foreign_keys="Document.author_id")
    comments = relationship("Comment", back_populates="user")
    favorites = relationship("UserFavorite", back_populates="user")
    likes = relationship("DocumentLike", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")
