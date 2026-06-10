from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from kiro.core.timezone_utils import get_beijing_time
from ..core.database import Base


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=get_beijing_time)

    user = relationship("User", back_populates="favorites")
    document = relationship("Document", back_populates="favorites")


class DocumentLike(Base):
    __tablename__ = "document_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=get_beijing_time)

    user = relationship("User", back_populates="likes")
    document = relationship("Document", back_populates="likes")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_beijing_time)

    user = relationship("User", back_populates="subscriptions")
