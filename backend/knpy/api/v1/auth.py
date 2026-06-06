from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ...core.database import get_db
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from ...schemas.common import TokenResponse, LoginRequest, RegisterRequest, RefreshTokenRequest
from ...schemas.user import UserResponse, UserCreate
from ...models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    existing_username = db.query(User).filter(User.username == request.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="用户名已被使用")

    user = User(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="账号未注册")

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout():
    return {"message": "退出成功"}
