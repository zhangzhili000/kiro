"""
SSO单点登录API路由
支持钉钉、企业微信、飞书登录
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from kiro_platform.core.database import get_db
from kiro_platform.core.security import create_access_token
from kiro_platform.schemas.user import Token
from kiro_platform.services.sso_service import DingTalkSSOService, WeChatWorkSSOService, FeishuSSOService

router = APIRouter(prefix="/sso", tags=["SSO登录"])


@router.get("/dingtalk/callback")
async def dingtalk_login(
    code: str = Query(..., description="钉钉授权码"),
    db: Session = Depends(get_db)
):
    """钉钉登录回调"""
    service = DingTalkSSOService(db)
    user = await service.login(code)
    
    if not user:
        raise HTTPException(status_code=401, detail="钉钉登录失败")
    
    # 生成JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/wechatwork/callback")
async def wechatwork_login(
    code: str = Query(..., description="企业微信授权码"),
    db: Session = Depends(get_db)
):
    """企业微信登录回调"""
    service = WeChatWorkSSOService(db)
    user = await service.login(code)
    
    if not user:
        raise HTTPException(status_code=401, detail="企业微信登录失败")
    
    # 生成JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/feishu/callback")
async def feishu_login(
    code: str = Query(..., description="飞书授权码"),
    db: Session = Depends(get_db)
):
    """飞书登录回调"""
    service = FeishuSSOService(db)
    user = await service.login(code)
    
    if not user:
        raise HTTPException(status_code=401, detail="飞书登录失败")
    
    # 生成JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return Token(access_token=access_token, token_type="bearer")
