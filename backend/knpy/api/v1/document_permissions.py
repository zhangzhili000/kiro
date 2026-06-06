from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from knpy.core.database import get_db
from knpy.api.v1.users import get_current_user
from knpy.models.user import User
from knpy.models.document import Document
from knpy.schemas.document_permission import DocumentPermissionResponse, DocumentPermissionsUpdate
from knpy.services.document_permission_service import (
    get_document_permissions_with_names,
    update_document_permissions,
    check_document_edit_permission
)

router = APIRouter(prefix="/documents/{document_id}/permissions", tags=["文档权限"])


@router.get("", response_model=List[DocumentPermissionResponse])
def get_permissions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档的所有权限"""
    return get_document_permissions_with_names(db, document_id)


@router.put("")
def update_permissions(
    document_id: int,
    permissions_update: DocumentPermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文档权限"""
    # 检查用户是否是文档作者或管理员
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改文档权限")
    
    update_document_permissions(db, document_id, permissions_update)
    return {"message": "权限更新成功"}


@router.get("/check-edit")
def check_edit_permission(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查当前用户是否有文档编辑权限"""
    has_permission = check_document_edit_permission(db, document_id, current_user.id)
    return {"has_permission": has_permission}