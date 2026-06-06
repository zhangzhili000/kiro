"""
SSO单点登录服务
支持钉钉、企业微信、飞书登录
"""
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from knpy.core.timezone_utils import get_beijing_time

from ..models.user import User
from ..models.department import Department
from ..schemas.user import UserCreate
from ..core.config import settings


class DingTalkSSOService:
    """钉钉SSO登录服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client_id = settings.DINGTALK_CLIENT_ID
        self.client_secret = settings.DINGTALK_CLIENT_SECRET
        self.redirect_uri = settings.DINGTALK_REDIRECT_URI
    
    async def get_access_token(self, code: str) -> Optional[str]:
        """获取钉钉access_token"""
        url = "https://oapi.dingtalk.com/sns/gettoken"
        params = {
            "appid": self.client_id,
            "appsecret": self.client_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("access_token")
            return None
    
    async def get_user_info(self, access_token: str, code: str) -> Optional[Dict[str, Any]]:
        """获取钉钉用户信息"""
        url = "https://oapi.dingtalk.com/sns/getuserinfo_bycode"
        params = {
            "access_token": access_token,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("user_info", {})
            return None
    
    async def login(self, code: str) -> Optional[User]:
        """钉钉登录流程"""
        # 1. 获取access_token
        access_token = await self.get_access_token(code)
        if not access_token:
            return None
        
        # 2. 获取用户信息
        user_info = await self.get_user_info(access_token, code)
        if not user_info:
            return None
        
        # 3. 创建或更新用户
        return self._create_or_update_user(user_info, "dingtalk")
    
    def _create_or_update_user(self, user_info: Dict[str, Any], provider: str) -> User:
        """创建或更新用户"""
        unionid = user_info.get("unionid") or user_info.get("openid")
        
        # 查找现有用户
        user = self.db.query(User).filter(
            User.sso_provider == provider,
            User.sso_id == unionid
        ).first()
        
        if user:
            # 更新用户信息
            if user_info.get("nick"):
                user.name = user_info["nick"]
            if user_info.get("avatar_url"):
                user.avatar = user_info["avatar_url"]
            self.db.commit()
            self.db.refresh(user)
            return user
        
        # 创建新用户
        new_user = User(
            email=f"{unionid}@{provider}.com",
            name=user_info.get("nick", "未知用户"),
            avatar=user_info.get("avatar_url"),
            role="user",
            sso_provider=provider,
            sso_id=unionid,
            is_active=True,
            created_at=get_beijing_time()
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user


class WeChatWorkSSOService:
    """企业微信SSO登录服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.corpid = settings.WECHATWORK_CORPID
        self.secret = settings.WECHATWORK_SECRET
        self.redirect_uri = settings.WECHATWORK_REDIRECT_URI
    
    async def get_access_token(self) -> Optional[str]:
        """获取企业微信access_token"""
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corpid,
            "corpsecret": self.secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("access_token")
            return None
    
    async def get_user_info(self, access_token: str, code: str) -> Optional[Dict[str, Any]]:
        """获取企业微信用户信息"""
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
        params = {
            "access_token": access_token,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            if data.get("errcode") == 0:
                return data
            return None
    
    async def login(self, code: str) -> Optional[User]:
        """企业微信登录流程"""
        # 1. 获取access_token
        access_token = await self.get_access_token()
        if not access_token:
            return None
        
        # 2. 获取用户信息
        user_info = await self.get_user_info(access_token, code)
        if not user_info:
            return None
        
        # 3. 创建或更新用户
        return self._create_or_update_user(user_info, "wechatwork")
    
    def _create_or_update_user(self, user_info: Dict[str, Any], provider: str) -> User:
        """创建或更新用户"""
        userid = user_info.get("UserId")
        
        if not userid:
            return None
        
        # 查找现有用户
        user = self.db.query(User).filter(
            User.sso_provider == provider,
            User.sso_id == userid
        ).first()
        
        if user:
            # 更新用户信息
            if user_info.get("Name"):
                user.name = user_info["Name"]
            if user_info.get("Avatar"):
                user.avatar = user_info["Avatar"]
            self.db.commit()
            self.db.refresh(user)
            return user
        
        # 创建新用户
        new_user = User(
            email=f"{userid}@{provider}.com",
            name=user_info.get("Name", "未知用户"),
            avatar=user_info.get("Avatar"),
            role="user",
            sso_provider=provider,
            sso_id=userid,
            is_active=True,
            created_at=get_beijing_time()
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user


class FeishuSSOService:
    """飞书SSO登录服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client_id = settings.FEISHU_CLIENT_ID
        self.client_secret = settings.FEISHU_CLIENT_SECRET
        self.redirect_uri = settings.FEISHU_REDIRECT_URI
    
    async def get_access_token(self, code: str) -> Optional[str]:
        """获取飞书access_token"""
        url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
        data = {
            "app_id": self.client_id,
            "app_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("access_token")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取飞书用户信息"""
        url = "https://open.feishu.cn/open-apis/authen/v1/user_info"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {})
            return None
    
    async def login(self, code: str) -> Optional[User]:
        """飞书登录流程"""
        # 1. 获取access_token
        access_token = await self.get_access_token(code)
        if not access_token:
            return None
        
        # 2. 获取用户信息
        user_info = await self.get_user_info(access_token)
        if not user_info:
            return None
        
        # 3. 创建或更新用户
        return self._create_or_update_user(user_info, "feishu")
    
    def _create_or_update_user(self, user_info: Dict[str, Any], provider: str) -> User:
        """创建或更新用户"""
        unionid = user_info.get("union_id")
        
        if not unionid:
            return None
        
        # 查找现有用户
        user = self.db.query(User).filter(
            User.sso_provider == provider,
            User.sso_id == unionid
        ).first()
        
        if user:
            # 更新用户信息
            if user_info.get("name"):
                user.name = user_info["name"]
            if user_info.get("avatar_url"):
                user.avatar = user_info["avatar_url"]
            self.db.commit()
            self.db.refresh(user)
            return user
        
        # 创建新用户
        new_user = User(
            email=f"{unionid}@{provider}.com",
            name=user_info.get("name", "未知用户"),
            avatar=user_info.get("avatar_url"),
            role="user",
            sso_provider=provider,
            sso_id=unionid,
            is_active=True,
            created_at=get_beijing_time()
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
