from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from kiro.core.timezone_utils import get_beijing_time
from ..core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    users = relationship("User", back_populates="department")
    parent = relationship("Department", remote_side=[id], backref="children")
