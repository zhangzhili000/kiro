from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from knpy.core.timezone_utils import get_beijing_time
from ..core.database import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    change_summary = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_beijing_time)

    document = relationship("Document", back_populates="versions")


class DocumentShare(Base):
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    share_token = Column(String(100), unique=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)

    document = relationship("Document", back_populates="shares")
