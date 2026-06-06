from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...core.security import decode_token
from ...schemas.user import UserResponse, UserUpdate, UserPasswordUpdate, UserListResponse
from ...models import User

router = APIRouter(prefix="/users", tags=["用户"])

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="未登录")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from knpy.models import Department
    department_name = None
    if current_user.department_id:
        dept = db.query(Department).filter(Department.id == current_user.department_id).first()
        if dept:
            department_name = dept.name
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "avatar": current_user.avatar,
        "phone": current_user.phone,
        "role": current_user.role,
        "department_id": current_user.department_id,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "department_name": department_name
    }


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
def change_password(
    password_update: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ...core.security import verify_password, get_password_hash
    if not verify_password(password_update.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    current_user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()
    return {"message": "密码修改成功"}


@router.post("/avatar")
def upload_avatar(
    avatar_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.avatar = avatar_url
    db.commit()
    return {"message": "头像上传成功", "avatar": avatar_url}
