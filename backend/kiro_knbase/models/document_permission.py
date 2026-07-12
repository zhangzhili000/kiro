from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from kiro_platform.core.timezone_utils import get_beijing_time
from kiro_platform.core.database import Base


class DocumentPermission(Base):
    """
    文档权限表 - 存储文档的精细权限控制
    
    支持两种权限类型：
    1. 团队级权限（team）：允许指定团队下的所有成员访问文档
    2. 用户级权限（user）：允许指定的具体用户访问文档
    
    支持三种操作类型：
    1. 查看权限（view）：可以查看文档内容
    2. 编辑权限（edit）：可以编辑文档内容
    3. 删除权限（delete）：可以删除文档
    """
    __tablename__ = "document_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    permission_type = Column(String(20), nullable=False)  # team, user
    target_id = Column(Integer, nullable=False)  # team_id 或 user_id
    action = Column(String(20), nullable=False)  # view, edit, delete
    created_at = Column(DateTime, default=get_beijing_time)
    
    document = relationship("Document", back_populates="permissions")
