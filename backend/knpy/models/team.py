from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from knpy.core.timezone_utils import get_beijing_time
from ..core.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_beijing_time)
    updated_at = Column(DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    members = relationship("TeamMember", back_populates="team")
    documents = relationship("TeamDocument", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # owner, admin, member
    joined_at = Column(DateTime, default=get_beijing_time)

    team = relationship("Team", back_populates="members")
    user = relationship("User")


class TeamDocument(Base):
    __tablename__ = "team_documents"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"))
    added_at = Column(DateTime, default=get_beijing_time)

    team = relationship("Team", back_populates="documents")
    document = relationship("Document")
    added_by_user = relationship("User")