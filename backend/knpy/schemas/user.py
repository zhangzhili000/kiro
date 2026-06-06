from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    department_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    department_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    department_name: Optional[str] = None

    class Config:
        from_attributes = True
