from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from kiro.core.timezone_utils import get_beijing_time
from ..core.database import Base


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    content = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    category = relationship("Category")
    created_by_user = relationship("User")