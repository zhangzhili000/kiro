from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from knpy.core.timezone_utils import get_beijing_time
from ..core.database import Base


class DocumentPermission(Base):
    """
    文档权限表 - 存储文档的精细权限控制
    
    支持两种权限类型：
    1. 部门级权限：允许指定部门下的所有用户编辑文档
    2. 用户级权限：允许指定的具体用户编辑文档
    """
    __tablename__ = "document_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    permission_type = Column(Integer, nullable=False)  # 1: 部门权限, 2: 用户权限
    target_id = Column(Integer, nullable=False)  # department_id 或 user_id
    created_at = Column(DateTime, default=get_beijing_time)
    
    document = relationship("Document", back_populates="permissions")