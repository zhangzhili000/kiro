from typing import List, Optional

from kiro_platform.core.database import SessionLocal
from kiro_platform.core.exceptions import NotFoundError
from kiro_platform.models.user import User
from kiro_platform.schemas.user import UserCreate, UserUpdate, UserResponse


def get_user(db, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_users(db, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db, user_create: UserCreate) -> User:
    from kiro_platform.services.auth_service import get_password_hash
    
    hashed_password = get_password_hash(user_create.password)
    user = User(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
        full_name=user_create.full_name,
        role=user_create.role or "user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db, user_id: int, user_update: UserUpdate) -> User:
    user = get_user(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.avatar is not None:
        user.avatar = user_update.avatar
    if user_update.phone is not None:
        user.phone = user_update.phone
    
    db.commit()
    db.refresh(user)
    return user


def delete_user(db, user_id: int) -> None:
    user = get_user(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    
    db.delete(user)
    db.commit()


def update_user_status(db, user_id: int, is_active: bool) -> User:
    user = get_user(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def get_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
