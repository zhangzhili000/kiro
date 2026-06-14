from pydantic import BaseModel
from typing import Optional, List


class DocumentPermissionCreate(BaseModel):
    """创建文档权限"""
    permission_type: int  # 1: 部门权限, 2: 用户权限
    target_id: int  # department_id 或 user_id


class DocumentPermissionUpdate(BaseModel):
    """更新文档权限"""
    permission_type: Optional[int] = None
    target_id: Optional[int] = None


class DocumentPermissionResponse(BaseModel):
    """文档权限响应"""
    id: int
    document_id: int
    permission_type: int
    target_id: int
    target_name: Optional[str] = None  # 部门名称或用户名


class DocumentPermissionsUpdate(BaseModel):
    """批量更新文档权限"""
    department_ids: List[int] = []  # 允许编辑的部门ID列表
    user_ids: List[int] = []  # 允许编辑的用户ID列表