"""
Coze Studio 集成服务

提供 Coze 集成的业务逻辑层，封装与 Coze 的交互细节，
为 Kiro 业务模块提供统一的 Coze 能力接口。

主要功能：
- 用户单点登录与同步
- 工作空间同步（Kiro 团队 ↔ Coze 工作空间）
- Agent 对话代理
- 知识库同步
- 工作流执行代理
"""
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator

from kiro_platform.core.config import settings
from kiro_platform.models.user import User
from kiro_platform.models.team import Team

from .coze_client import get_coze_client, CozeClient

logger = logging.getLogger(__name__)


class CozeService:
    """
    Coze 集成服务
    
    提供业务层面的 Coze 集成能力，封装底层 API 调用细节。
    """

    def __init__(self):
        self.client: CozeClient = get_coze_client()

    def is_enabled(self) -> bool:
        """检查 Coze 集成是否启用"""
        return self.client.is_enabled()

    # ============== 用户单点登录 ==============

    def generate_sso_token(
        self,
        user: User,
        team: Optional[Team] = None,
        expires_hours: int = 24
    ) -> str:
        """
        为指定用户生成 Coze 单点登录 Token
        
        Args:
            user: Kiro 用户对象
            team: 所属团队（映射为 Coze 工作空间）
            expires_hours: Token 有效期（小时）
            
        Returns:
            JWT Token 字符串
        """
        workspace_id = ""
        if team:
            workspace_id = self._get_workspace_id(team)

        return self.client.generate_sso_token(
            user_id=str(user.id),
            username=user.username,
            email=user.email or "",
            workspace_id=workspace_id,
            expires_hours=expires_hours
        )

    def get_sso_url(
        self,
        user: User,
        team: Optional[Team] = None,
        redirect_path: str = "/"
    ) -> str:
        """
        生成带 SSO Token 的 Coze 访问 URL
        
        Args:
            user: 用户对象
            team: 团队对象
            redirect_path: 跳转路径
            
        Returns:
            完整的 Coze 访问 URL
        """
        token = self.generate_sso_token(user, team)
        base_url = settings.COZE_BASE_URL.rstrip("/")
        # 移除路径中的前导斜杠，避免双斜杠
        path = redirect_path.lstrip("/")
        return f"{base_url}/{path}?kiro_sso_token={token}"

    # ============== 用户同步 ==============

    async def sync_user_to_coze(self, user: User) -> Optional[Dict[str, Any]]:
        """
        同步用户信息到 Coze
        
        如果 Coze 中不存在该用户，则创建；如果存在，则更新信息。
        
        Args:
            user: Kiro 用户对象
            
        Returns:
            Coze 用户信息，失败返回 None
        """
        if not self.is_enabled():
            logger.warning("Coze is not enabled, skip user sync")
            return None

        try:
            result = await self.client.sync_user(
                user_id=str(user.id),
                username=user.username,
                email=user.email or "",
                avatar_url=user.avatar_url or ""
            )
            logger.info(f"User {user.id} synced to Coze successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to sync user {user.id} to Coze: {e}")
            return None

    # ============== 工作空间同步 ==============

    def _get_workspace_id(self, team: Team) -> str:
        """
        获取团队对应的 Coze 工作空间 ID
        
        优先使用 team 的 coze_workspace_id 字段，
        如果没有则使用 team.id 作为外部标识。
        
        Args:
            team: 团队对象
            
        Returns:
            工作空间 ID
        """
        # TODO: 可以在 team 模型中增加 coze_workspace_id 字段
        # 这里先用团队 ID 作为标识
        return f"kiro_team_{team.id}"

    async def sync_team_to_workspace(self, team: Team, owner: User) -> Optional[Dict[str, Any]]:
        """
        同步 Kiro 团队到 Coze 工作空间
        
        Args:
            team: Kiro 团队对象
            owner: 团队所有者
            
        Returns:
            Coze 工作空间信息
        """
        if not self.is_enabled():
            logger.warning("Coze is not enabled, skip team sync")
            return None

        try:
            workspace = await self.client.create_workspace(
                name=team.name,
                description=team.description or "",
                owner_id=str(owner.id)
            )
            logger.info(f"Team {team.id} synced to Coze workspace")
            return workspace
        except Exception as e:
            logger.error(f"Failed to sync team {team.id} to Coze: {e}")
            return None

    # ============== Agent 对话 ==============

    async def chat_with_agent(
        self,
        query: str,
        user: User,
        agent_id: Optional[str] = None,
        conversation_id: str = "",
        use_default_agent: bool = True
    ) -> Dict[str, Any]:
        """
        使用 Coze Agent 进行对话（非流式）
        
        Args:
            query: 用户问题
            user: 用户对象
            agent_id: Agent ID（不传则使用默认 Agent）
            conversation_id: 会话 ID（续传时使用）
            use_default_agent: 是否使用默认 Agent
            
        Returns:
            对话结果
        """
        if not self.is_enabled():
            raise RuntimeError("Coze is not enabled")

        target_agent_id = agent_id or settings.COZE_DEFAULT_AGENT_ID
        if not target_agent_id and use_default_agent:
            raise ValueError("No agent specified and no default agent configured")

        # 确保用户已同步到 Coze
        await self.sync_user_to_coze(user)

        result = await self.client.create_conversation(
            agent_id=target_agent_id,
            query=query,
            user_id=str(user.id),
            conversation_id=conversation_id,
            additional_variables={
                "kiro_user_id": str(user.id),
                "kiro_username": user.username,
            }
        )
        return result

    async def chat_with_agent_stream(
        self,
        query: str,
        user: User,
        agent_id: Optional[str] = None,
        conversation_id: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        使用 Coze Agent 进行流式对话
        
        Args:
            query: 用户问题
            user: 用户对象
            agent_id: Agent ID
            conversation_id: 会话 ID
            
        Yields:
            流式事件数据
        """
        if not self.is_enabled():
            raise RuntimeError("Coze is not enabled")

        target_agent_id = agent_id or settings.COZE_DEFAULT_AGENT_ID
        if not target_agent_id:
            raise ValueError("No agent specified and no default agent configured")

        # 确保用户已同步到 Coze
        await self.sync_user_to_coze(user)

        async for event in self.client.create_conversation_stream(
            agent_id=target_agent_id,
            query=query,
            user_id=str(user.id),
            conversation_id=conversation_id,
            additional_variables={
                "kiro_user_id": str(user.id),
                "kiro_username": user.username,
            }
        ):
            yield event

    # ============== 知识库同步 ==============

    async def sync_document_to_coze(
        self,
        document_id: int,
        document_title: str,
        document_content: str,
        team: Optional[Team] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        同步文档到 Coze 知识库
        
        Args:
            document_id: 文档 ID
            document_title: 文档标题
            document_content: 文档内容
            team: 所属团队
            metadata: 附加元数据
            
        Returns:
            Coze 文档信息
        """
        if not self.is_enabled():
            logger.warning("Coze is not enabled, skip document sync")
            return None

        try:
            # 获取知识库 ID（按团队划分知识库）
            knowledge_id = await self._get_or_create_knowledge_base(team)
            if not knowledge_id:
                logger.error("Failed to get or create knowledge base")
                return None

            # 合并元数据
            doc_metadata = {
                "kiro_document_id": document_id,
                **(metadata or {})
            }

            result = await self.client.upload_document(
                knowledge_id=knowledge_id,
                title=document_title,
                content=document_content,
                document_type="text",
                metadata=doc_metadata
            )
            logger.info(f"Document {document_id} synced to Coze")
            return result
        except Exception as e:
            logger.error(f"Failed to sync document {document_id} to Coze: {e}")
            return None

    async def _get_or_create_knowledge_base(self, team: Optional[Team]) -> str:
        """
        获取或创建知识库
        
        按团队划分知识库，每个团队对应一个知识库。
        
        Args:
            team: 团队对象
            
        Returns:
            知识库 ID
        """
        # TODO: 实现知识库的缓存和持久化
        # 简单实现：使用默认知识库或创建新的
        # 后续可以在数据库中存储团队与知识库的映射关系
        if team:
            kb_name = f"Team {team.name} Knowledge Base"
            try:
                result = await self.client.create_knowledge_base(
                    name=kb_name,
                    description=f"Knowledge base for team {team.name}",
                    workspace_id=self._get_workspace_id(team)
                )
                return result.get("data", {}).get("id", "")
            except Exception:
                # 如果创建失败（可能已存在），返回空字符串，由上层处理
                pass

        return settings.COZE_DEFAULT_WORKSPACE_ID

    # ============== 工作流执行 ==============

    async def execute_workflow(
        self,
        workflow_id: str,
        params: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """
        执行 Coze 工作流
        
        Args:
            workflow_id: 工作流 ID
            params: 工作流参数
            user: 执行用户
            
        Returns:
            执行结果
        """
        if not self.is_enabled():
            raise RuntimeError("Coze is not enabled")

        # 确保用户已同步
        await self.sync_user_to_coze(user)

        return await self.client.run_workflow(
            workflow_id=workflow_id,
            params=params,
            user_id=str(user.id)
        )

    # ============== 插件/Skill 同步 ==============

    async def list_coze_plugins(
        self,
        team: Optional[Team] = None
    ) -> List[Dict[str, Any]]:
        """
        获取 Coze 插件列表（用于同步到 Kiro Skill 市场）
        
        Args:
            team: 团队对象
            
        Returns:
            插件列表
        """
        if not self.is_enabled():
            return []

        try:
            workspace_id = self._get_workspace_id(team) if team else ""
            plugins = await self.client.list_plugins(workspace_id=workspace_id)
            return plugins
        except Exception as e:
            logger.error(f"Failed to list Coze plugins: {e}")
            return []

    # ============== 健康检查 ==============

    async def check_health(self) -> Dict[str, Any]:
        """
        检查 Coze 服务健康状态
        
        Returns:
            健康状态信息
        """
        if not self.is_enabled():
            return {
                "enabled": False,
                "status": "disabled",
                "message": "Coze integration is not enabled"
            }

        is_healthy = await self.client.health_check()
        return {
            "enabled": True,
            "status": "healthy" if is_healthy else "unhealthy",
            "base_url": settings.COZE_BASE_URL,
        }


# 全局单例
_coze_service: Optional[CozeService] = None


def get_coze_service() -> CozeService:
    """获取 Coze 服务单例"""
    global _coze_service
    if _coze_service is None:
        _coze_service = CozeService()
    return _coze_service


__all__ = [
    "CozeService",
    "get_coze_service",
]
