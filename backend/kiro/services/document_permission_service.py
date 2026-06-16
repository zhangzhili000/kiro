from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from kiro.core.exceptions import NotFoundError
from kiro.models.document_permission import DocumentPermission
from kiro.models.document import Document
from kiro.models.user import User
from kiro.models.department import Department
from kiro.models.team import Team, TeamMember
from kiro.schemas.document_permission import (
    DocumentPermissionCreate, 
    DocumentPermissionsUpdate,
    PermissionType,
    PermissionAction
)


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
        if perm.permission_type == PermissionType.DEPARTMENT.value:
            # 部门权限
            dept = db.query(Department).filter(Department.id == perm.target_id).first()
            target_name = dept.name if dept else None
        elif perm.permission_type == PermissionType.TEAM.value:
            # 团队权限
            team = db.query(Team).filter(Team.id == perm.target_id).first()
            target_name = team.name if team else None
        elif perm.permission_type == PermissionType.USER.value:
            # 用户权限
            user = db.query(User).filter(User.id == perm.target_id).first()
            target_name = user.username if user else None
        
        result.append({
            "id": perm.id,
            "document_id": perm.document_id,
            "permission_type": perm.permission_type,
            "target_id": perm.target_id,
            "action": perm.action,
            "target_name": target_name
        })
    
    return result


def create_document_permission(db: Session, permission: DocumentPermissionCreate, document_id: int) -> DocumentPermission:
    """创建文档权限"""
    doc_perm = DocumentPermission(
        document_id=document_id,
        permission_type=permission.permission_type.value,
        target_id=permission.target_id,
        action=permission.action.value
    )
    db.add(doc_perm)
    db.commit()
    db.refresh(doc_perm)
    return doc_perm


def update_document_permissions(db: Session, document_id: int, permissions_update: DocumentPermissionsUpdate) -> None:
    """批量更新文档权限"""
    # 删除所有现有权限
    db.query(DocumentPermission).filter(DocumentPermission.document_id == document_id).delete()
    
    # 添加新的权限
    for perm_item in permissions_update.permissions:
        doc_perm = DocumentPermission(
            document_id=document_id,
            permission_type=perm_item.permission_type.value,
            target_id=perm_item.target_id,
            action=perm_item.action.value
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


def check_user_in_team(db: Session, user_id: int, team_id: int) -> bool:
    """检查用户是否在团队中"""
    team_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    return team_member is not None


def check_document_view_permission(db: Session, document_id: int, user_id: int) -> bool:
    """检查用户是否有文档查看权限"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return False
    
    # 文档作者有所有权限
    if document.author_id == user_id:
        return True
    
    # public 文档：所有用户可查看
    if document.permission == "public":
        return True
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # 获取文档的权限列表
    permissions = get_document_permissions(db, document_id)
    
    for perm in permissions:
        # 查看、编辑、删除权限都包含查看权限
        if perm.action in [PermissionAction.VIEW.value, PermissionAction.EDIT.value, PermissionAction.DELETE.value]:
            # 部门权限：检查用户是否在该部门
            if perm.permission_type == PermissionType.DEPARTMENT.value:
                if user.department_id == perm.target_id:
                    return True
            # 团队权限：检查用户是否是该团队成员
            elif perm.permission_type == PermissionType.TEAM.value:
                if check_user_in_team(db, user_id, perm.target_id):
                    return True
            # 用户权限：检查用户ID是否匹配
            elif perm.permission_type == PermissionType.USER.value:
                if user.id == perm.target_id:
                    return True
    
    return False


def check_document_edit_permission(db: Session, document_id: int, user_id: int) -> bool:
    """检查用户是否有文档编辑权限"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return False
    
    # 文档作者有所有权限
    if document.author_id == user_id:
        return True
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # 获取文档的权限列表
    permissions = get_document_permissions(db, document_id)
    
    for perm in permissions:
        # 编辑、删除权限都包含编辑权限
        if perm.action in [PermissionAction.EDIT.value, PermissionAction.DELETE.value]:
            # 部门权限：检查用户是否在该部门
            if perm.permission_type == PermissionType.DEPARTMENT.value:
                if user.department_id == perm.target_id:
                    return True
            # 团队权限：检查用户是否是该团队成员
            elif perm.permission_type == PermissionType.TEAM.value:
                if check_user_in_team(db, user_id, perm.target_id):
                    return True
            # 用户权限：检查用户ID是否匹配
            elif perm.permission_type == PermissionType.USER.value:
                if user.id == perm.target_id:
                    return True
    
    return False


def check_document_delete_permission(db: Session, document_id: int, user_id: int) -> bool:
    """检查用户是否有文档删除权限"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        return False
    
    # 文档作者有所有权限
    if document.author_id == user_id:
        return True
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # 获取文档的权限列表
    permissions = get_document_permissions(db, document_id)
    
    for perm in permissions:
        # 只有删除权限才能删除
        if perm.action == PermissionAction.DELETE.value:
            # 部门权限：检查用户是否在该部门
            if perm.permission_type == PermissionType.DEPARTMENT.value:
                if user.department_id == perm.target_id:
                    return True
            # 团队权限：检查用户是否是该团队成员
            elif perm.permission_type == PermissionType.TEAM.value:
                if check_user_in_team(db, user_id, perm.target_id):
                    return True
            # 用户权限：检查用户ID是否匹配
            elif perm.permission_type == PermissionType.USER.value:
                if user.id == perm.target_id:
                    return True
    
    return False


def get_documents_with_view_permission(db: Session, user_id: int) -> List[Document]:
    """获取用户有查看权限的所有文档"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # 获取用户所在团队的ID列表
    team_members = db.query(TeamMember).filter(TeamMember.user_id == user_id).all()
    team_ids = [tm.team_id for tm in team_members]
    
    # 构建权限查询条件
    conditions = []
    
    # 部门权限条件
    if user.department_id:
        conditions.append(
            db.query(DocumentPermission.document_id).filter(
                DocumentPermission.permission_type == PermissionType.DEPARTMENT.value,
                DocumentPermission.target_id == user.department_id,
                DocumentPermission.action.in_([
                    PermissionAction.VIEW.value,
                    PermissionAction.EDIT.value,
                    PermissionAction.DELETE.value
                ])
            )
        )
    
    # 团队权限条件
    if team_ids:
        conditions.append(
            db.query(DocumentPermission.document_id).filter(
                DocumentPermission.permission_type == PermissionType.TEAM.value,
                DocumentPermission.target_id.in_(team_ids),
                DocumentPermission.action.in_([
                    PermissionAction.VIEW.value,
                    PermissionAction.EDIT.value,
                    PermissionAction.DELETE.value
                ])
            )
        )
    
    # 用户权限条件
    conditions.append(
        db.query(DocumentPermission.document_id).filter(
            DocumentPermission.permission_type == PermissionType.USER.value,
            DocumentPermission.target_id == user_id,
            DocumentPermission.action.in_([
                PermissionAction.VIEW.value,
                PermissionAction.EDIT.value,
                PermissionAction.DELETE.value
            ])
        )
    )
    
    # 合并所有权限对应的文档ID
    document_ids = set()
    for condition_query in conditions:
        for doc_id in condition_query.all():
            document_ids.add(doc_id[0])
    
    # 获取文档
    if document_ids:
        docs = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.status == "published",
            Document.is_deleted == False
        ).all()
    else:
        docs = []
    
    return docs


def get_documents_for_ai_query(db: Session, user_id: int) -> List[Document]:
    """获取用户有权限访问的文档用于AI问答"""
    # 获取所有公开文档
    public_docs = db.query(Document).filter(
        Document.permission == "public",
        Document.status == "published",
        Document.is_deleted == False
    ).all()
    
    # 获取用户作为作者的文档
    author_docs = db.query(Document).filter(
        Document.author_id == user_id,
        Document.status == "published",
        Document.is_deleted == False
    ).all()
    
    # 获取用户有权限的文档（通过 DocumentPermission）
    permission_docs = get_documents_with_view_permission(db, user_id)
    
    # 合并去重
    all_docs = list(set(public_docs + author_docs + permission_docs))
    
    return all_docs