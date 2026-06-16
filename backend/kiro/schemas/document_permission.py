from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PermissionType(str, Enum):
    DEPARTMENT = "department"
    TEAM = "team"
    USER = "user"


class PermissionAction(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"


class DocumentPermissionCreate(BaseModel):
    """创建文档权限"""
    permission_type: PermissionType
    target_id: int
    action: PermissionAction = Field(default=PermissionAction.VIEW)


class DocumentPermissionUpdate(BaseModel):
    """更新文档权限"""
    permission_type: Optional[PermissionType] = None
    target_id: Optional[int] = None
    action: Optional[PermissionAction] = None


class DocumentPermissionResponse(BaseModel):
    """文档权限响应"""
    id: int
    document_id: int
    permission_type: str
    target_id: int
    action: str
    target_name: Optional[str] = None


class DocumentPermissionItem(BaseModel):
    """文档权限项"""
    permission_type: PermissionType
    target_id: int
    action: PermissionAction


class DocumentPermissionsUpdate(BaseModel):
    """批量更新文档权限"""
    permissions: List[DocumentPermissionItem] = []