from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from kiro.core.exceptions import NotFoundError
from kiro.models.document_permission import DocumentPermission
from kiro.models.document import Document
from kiro.models.user import User
from kiro.models.department import Department
from kiro.schemas.document_permission import DocumentPermissionCreate, DocumentPermissionsUpdate


def get_document_permission(db: Session, permission_id: int) -> Optional[DocumentPermission]:
    """获取单个文档权限"""
    return db.query(DocumentPermission).filter(DocumentPermission.id == permission_id).first()


def get_document_permissions(db: Session, document_id: int) -> List[DocumentPermission]:
    """获取文档的所有权限"""
    return db.query(DocumentPermission).filter(DocumentPermission.document_id == document_id).all()


def get_document_permissions_with_names(db: Session, document_id: int) -> List[dict]:
    """获取文档的所有权限（带名称）"""
    permissions = get_document_permissions(db, document_id)
    result = []
    
    for perm in permissions:
        target_name = None
        if perm.permission_type == 1:
            # 部门权限
            dept = db.query(Department).filter(Department.id == perm.target_id).first()
            target_name = dept.name if dept else None
        elif perm.permission_type == 2:
            # 用户权限
            user = db.query(User).filter(User.id == perm.target_id).first()
            target_name = user.username if user else None
        
        result.append({
            "id": perm.id,
            "document_id": perm.document_id,
            "permission_type": perm.permission_type,
            "target_id": perm.target_id,
            "target_name": target_name
        })
    
    return result


def create_document_permission(db: Session, permission: DocumentPermissionCreate, document_id: int) -> DocumentPermission:
    """创建文档权限"""
    doc_perm = DocumentPermission(
        document_id=document_id,
        permission_type=permission.permission_type,
        target_id=permission.target_id
    )
    db.add(doc_perm)
    db.commit()
    db.refresh(doc_perm)
    return doc_perm


def update_document_permissions(db: Session, document_id: int, permissions_update: DocumentPermissionsUpdate) -> None:
    """批量更新文档权限"""
    # 删除所有现有权限
    db.query(DocumentPermission).filter(DocumentPermission.document_id == document_id).delete()
    
    # 添加新的部门权限
    for dept_id in permissions_update.department_ids:
        doc_perm = DocumentPermission(
            document_id=document_id,
            permission_type=1,  # 部门权限
            target_id=dept_id
        )
        db.add(doc_perm)
    
    # 添加新的用户权限
    for user_id in permissions_update.user_ids:
        doc_perm = DocumentPermission(
            document_id=document_id,
            permission_type=2,  # 用户权限
            target_id=user_id
        )
        db.add(doc_perm)
    
    db.commit()


def delete_document_permission(db: Session, permission_id: int) -> None:
    """删除文档权限"""
    perm = get_document_permission(db, permission_id)
    if not perm:
        raise NotFoundError("权限不存在")
    
    db.delete(perm)
    db.commit()


def check_document_edit_permission(db: Session, document_id: int, user_id: int) -> bool:
    """检查用户是否有文档编辑权限"""
    # 先获取文档信息
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return False
    
    # 文档作者有编辑权限
    if document.author_id == user_id:
        return True
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # 获取文档的权限列表
    permissions = get_document_permissions(db, document_id)
    
    for perm in permissions:
        if perm.permission_type == 1:
            # 部门权限：检查用户是否在该部门
            if user.department_id == perm.target_id:
                return True
        elif perm.permission_type == 2:
            # 用户权限：检查用户ID是否匹配
            if user.id == perm.target_id:
                return True
    
    return False