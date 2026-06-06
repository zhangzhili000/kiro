from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ....core.database import get_db
from ..users import get_current_user
from ....models.user import User
from ....schemas.role import RoleResponse, RoleCreate, RoleUpdate
from ....services.role_service import (
    create_role, update_role, delete_role, get_roles, get_role, get_role_by_code,
    get_all_roles_with_permissions, get_role_with_permissions
)

router = APIRouter(prefix="/admin/roles", tags=["管理员-角色"])


def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无管理员权限")
    return current_user


@router.get("", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    return get_all_roles_with_permissions(db)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role_detail(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    role = get_role_with_permissions(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@router.post("", response_model=RoleResponse)
def add_role(
    role_create: RoleCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    try:
        create_role(db, role_create)
        return get_role_with_permissions(db, get_role_by_code(db, role_create.code).id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{role_id}", response_model=RoleResponse)
def modify_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    try:
        update_role(db, role_id, role_update)
        return get_role_with_permissions(db, role_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{role_id}")
def remove_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    try:
        delete_role(db, role_id)
        return {"message": "角色已删除"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))