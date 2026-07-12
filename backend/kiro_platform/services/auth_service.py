from datetime import datetime, timedelta
from ..core.timezone_utils import get_beijing_time
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from kiro_platform.core.config import settings
from kiro_platform.core.database import SessionLocal
from kiro_platform.core.exceptions import AuthenticationError
from kiro_platform.models.user import User
from kiro_platform.schemas.user import TokenData, UserCreate, UserUpdate


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = get_beijing_time() + expires_delta
    else:
        expire = get_beijing_time() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def authenticate_user(db, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_email(db, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db, user_create: UserCreate) -> User:
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
    user = get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User not found")
    
    if user_update.username:
        user.username = user_update.username
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.role:
        user.role = user_update.role
    
    db.commit()
    db.refresh(user)
    return user


def update_user_status(db, user_id: int, is_active: bool) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User not found")
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def get_current_user(token: str) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise AuthenticationError("Could not validate credentials")
        token_data = TokenData(email=email)
    except JWTError:
        raise AuthenticationError("Could not validate credentials")
    
    db = SessionLocal()
    try:
        user = get_user_by_email(db, email=token_data.email)
        if user is None:
            raise AuthenticationError("User not found")
        return user
    finally:
        db.close()
