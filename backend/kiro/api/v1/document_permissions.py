from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from kiro.core.database import get_db
from kiro.api.v1.users import get_current_user
from kiro.models.user import User
from kiro.models.document import Document
from kiro.schemas.document_permission import (
    DocumentPermissionResponse, 
    DocumentPermissionsUpdate,
    DocumentPermissionCreate
)
from kiro.services.document_permission_service import (
    get_document_permissions_with_names,
    update_document_permissions,
    create_document_permission,
    delete_document_permission,
    check_document_view_permission,
    check_document_edit_permission,
    check_document_delete_permission,
    get_document_permission
)

router = APIRouter(prefix="/documents/{document_id}/permissions", tags=["文档权限"])


@router.get("", response_model=List[DocumentPermissionResponse])
def get_permissions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档的所有权限"""
    # 检查用户是否有查看权限
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 只有文档作者或有查看权限的用户才能查看权限列表
    if document.author_id != current_user.id and current_user.role != "admin":
        if not check_document_view_permission(db, document_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限查看文档权限")
    
    return get_document_permissions_with_names(db, document_id)


@router.post("")
def add_permission(
    document_id: int,
    permission: DocumentPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加单个权限"""
    # 检查用户是否是文档作者或管理员
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改文档权限")
    
    # 创建权限
    new_permission = create_document_permission(db, permission, document_id)
    return {"message": "权限添加成功", "permission_id": new_permission.id}


@router.put("")
def update_permissions(
    document_id: int,
    permissions_update: DocumentPermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新文档权限"""
    # 检查用户是否是文档作者或管理员
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改文档权限")
    
    update_document_permissions(db, document_id, permissions_update)
    return {"message": "权限更新成功"}


@router.delete("/{permission_id}")
def remove_permission(
    document_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除单个权限"""
    # 检查用户是否是文档作者或管理员
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改文档权限")
    
    # 检查权限是否存在且属于该文档
    permission = get_document_permission(db, permission_id)
    if not permission or permission.document_id != document_id:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    delete_document_permission(db, permission_id)
    return {"message": "权限删除成功"}


@router.get("/check-view")
def check_view_permission_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查当前用户是否有文档查看权限"""
    has_permission = check_document_view_permission(db, document_id, current_user.id)
    return {"has_permission": has_permission}


@router.get("/check-edit")
def check_edit_permission_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查当前用户是否有文档编辑权限"""
    has_permission = check_document_edit_permission(db, document_id, current_user.id)
    return {"has_permission": has_permission}


@router.get("/check-delete")
def check_delete_permission_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查当前用户是否有文档删除权限"""
    has_permission = check_document_delete_permission(db, document_id, current_user.id)
    return {"has_permission": has_permission}