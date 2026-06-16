from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from kiro.core.database import Base
from kiro.core.timezone_utils import get_beijing_time

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text)
    html_content = Column(Text)
    summary = Column(Text)
    keywords = Column(JSON)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    permission = Column(String(20), default="public")
    department_id = Column(Integer, ForeignKey("departments.id"))
    status = Column(String(20), default="draft")  # draft, pending_review, published, rejected
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 记录删除者
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    author = relationship("User", back_populates="documents", foreign_keys=[author_id])
    category = relationship("Category", back_populates="documents")
    department = relationship("Department")
    tags = relationship("DocumentTag", back_populates="document")
    versions = relationship("DocumentVersion", back_populates="document")
    comments = relationship("Comment", back_populates="document")
    favorites = relationship("UserFavorite", back_populates="document")
    likes = relationship("DocumentLike", back_populates="document")
    shares = relationship("DocumentShare", back_populates="document")
    graph_node = relationship("KnowledgeGraphNode", back_populates="document", uselist=False)
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
