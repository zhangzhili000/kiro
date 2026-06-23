from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, DateTime, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from kiro.core.timezone_utils import get_beijing_time
from ..core.database import Base

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    content_type = Column(String(100))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_beijing_time)

    document = relationship("Document")
    uploaded_by_user = relationship("User")