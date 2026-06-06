import json
from typing import List, Optional

from knpy.core.exceptions import NotFoundError
from knpy.models.role import Role
from knpy.schemas.role import RoleCreate, RoleUpdate


def get_role(db, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_code(db, code: str) -> Optional[Role]:
    return db.query(Role).filter(Role.code == code).first()


def get_roles(db, skip: int = 0, limit: int = 100) -> List[Role]:
    return db.query(Role).offset(skip).limit(limit).all()


def create_role(db, role_create: RoleCreate) -> Role:
    # 检查角色代码是否已存在
    existing_role = get_role_by_code(db, role_create.code)
    if existing_role:
        raise ValueError(f"角色代码 {role_create.code} 已存在")
    
    permissions_json = json.dumps(role_create.permissions)
    
    role = Role(
        name=role_create.name,
        code=role_create.code,
        description=role_create.description,
        permissions=permissions_json
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db, role_id: int, role_update: RoleUpdate) -> Role:
    role = get_role(db, role_id)
    if not role:
        raise NotFoundError("角色不存在")
    
    if role_update.name:
        role.name = role_update.name
    if role_update.description:
        role.description = role_update.description
    if role_update.permissions is not None:
        role.permissions = json.dumps(role_update.permissions)
    
    db.commit()
    db.refresh(role)
    return role


def delete_role(db, role_id: int) -> None:
    role = get_role(db, role_id)
    if not role:
        raise NotFoundError("角色不存在")
    
    db.delete(role)
    db.commit()


def get_role_with_permissions(db, role_id: int) -> Optional[dict]:
    role = get_role(db, role_id)
    if not role:
        return None
    
    try:
        permissions = json.loads(role.permissions) if role.permissions else []
    except json.JSONDecodeError:
        permissions = []
    
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "permissions": permissions,
        "created_at": role.created_at,
        "updated_at": role.updated_at
    }


def get_all_roles_with_permissions(db) -> List[dict]:
    roles = get_roles(db)
    result = []
    for role in roles:
        try:
            permissions = json.loads(role.permissions) if role.permissions else []
        except json.JSONDecodeError:
            permissions = []
        
        result.append({
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "permissions": permissions,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        })
    return result