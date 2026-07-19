"""
Coze Studio 集成 API

提供与 Coze Studio 集成相关的 API 接口，包括：
- 单点登录 Token 获取
- 用户同步
- 健康检查
- 配置信息获取
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from kiro_platform.api.v1.users import get_current_user
from kiro_platform.models.user import User
from kiro_platform.core.config import settings

from kiro_knbase.services.coze_service import get_coze_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coze", tags=["Coze 集成"])


@router.get("/health")
async def coze_health_check():
    """
    检查 Coze 集成状态
    
    返回 Coze 服务的健康状态和配置信息。
    """
    coze_service = get_coze_service()
    result = await coze_service.check_health()
    return result


@router.get("/config")
async def get_coze_config(
    current_user: User = Depends(get_current_user)
):
    """
    获取 Coze 集成配置（仅返回前端需要的公开配置）
    
    返回 Coze 集成是否启用、基础 URL 等前端需要的配置信息。
    不返回敏感信息（如 API Key、共享密钥等）。
    """
    return {
        "enabled": settings.COZE_ENABLED,
        "base_url": settings.COZE_BASE_URL,
        "default_agent_id": settings.COZE_DEFAULT_AGENT_ID,
    }


@router.post("/sso/token")
async def generate_coze_sso_token(
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    生成 Coze 单点登录 Token
    
    为当前用户生成用于 Coze 自动登录的 JWT Token。
    Token 使用共享密钥签名，Coze 端验证后自动登录或注册用户。
    
    Args:
        team_id: 团队 ID（可选，用于指定工作空间）
    
    Returns:
        SSO Token 及相关信息
    """
    if not settings.COZE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coze integration is not enabled"
        )

    coze_service = get_coze_service()
    
    # TODO: 根据 team_id 获取团队对象
    team = None
    
    token = coze_service.generate_sso_token(
        user=current_user,
        team=team
    )
    
    return {
        "token": token,
        "base_url": settings.COZE_BASE_URL,
        "expires_in": 24 * 3600,  # 24小时
    }


@router.get("/sso/redirect")
async def coze_sso_redirect(
    redirect_path: str = "/",
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    跳转到 Coze（自动携带 SSO Token）
    
    生成带 SSO Token 的 URL 并重定向到 Coze，实现单点登录。
    
    Args:
        redirect_path: 在 Coze 中的跳转路径
        team_id: 团队 ID
    """
    if not settings.COZE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coze integration is not enabled"
        )

    coze_service = get_coze_service()
    
    # TODO: 根据 team_id 获取团队对象
    team = None
    
    redirect_url = coze_service.get_sso_url(
        user=current_user,
        team=team,
        redirect_path=redirect_path
    )
    
    return RedirectResponse(url=redirect_url)


@router.post("/sync/user")
async def sync_current_user_to_coze(
    current_user: User = Depends(get_current_user)
):
    """
    同步当前用户到 Coze
    
    将当前登录用户的信息同步到 Coze，首次同步时会创建 Coze 用户。
    """
    if not settings.COZE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coze integration is not enabled"
        )

    coze_service = get_coze_service()
    result = await coze_service.sync_user_to_coze(current_user)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync user to Coze"
        )
    
    return {
        "message": "User synced successfully",
        "data": result
    }


@router.get("/plugins")
async def list_coze_plugins(
    current_user: User = Depends(get_current_user)
):
    """
    获取 Coze 插件列表
    
    返回 Coze 中可用的插件列表，可用于同步到 Kiro Skill 市场。
    """
    if not settings.COZE_ENABLED:
        return {"enabled": False, "plugins": []}

    coze_service = get_coze_service()
    plugins = await coze_service.list_coze_plugins()
    
    return {
        "enabled": True,
        "total": len(plugins),
        "plugins": plugins
    }
