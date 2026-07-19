"""
Coze Studio API 客户端封装

提供与 Coze Studio 交互的统一 API 接口，包括：
- 用户认证与 Token 生成
- Agent 对话
- 知识库管理
- 工作流执行
- 插件管理
"""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import httpx
from jose import jwt

from kiro_platform.core.config import settings

logger = logging.getLogger(__name__)


class CozeClient:
    """
    Coze Studio API 客户端
    
    封装 Coze Studio 的 OpenAPI 调用，提供统一的接口供业务层使用。
    支持：
    - 用户认证与单点登录
    - Agent 对话（流式/非流式）
    - 知识库管理
    - 工作流执行
    - 插件管理
    """

    def __init__(self):
        self.base_url = settings.COZE_BASE_URL.rstrip("/")
        self.api_key = settings.COZE_API_KEY
        self.timeout = settings.COZE_TIMEOUT
        self.shared_secret = settings.COZE_SHARED_SECRET
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_default_headers()
            )
        return self._client

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_enabled(self) -> bool:
        """检查 Coze 集成是否启用"""
        return settings.COZE_ENABLED and bool(self.base_url)

    # ============== 用户认证相关 ==============

    def generate_sso_token(
        self,
        user_id: str,
        username: str = "",
        email: str = "",
        workspace_id: str = "",
        expires_hours: int = 24
    ) -> str:
        """
        生成 Coze 单点登录 Token
        
        使用共享密钥生成 JWT Token，Coze 端验证后自动登录或注册用户。
        
        Args:
            user_id: Kiro 用户 ID
            username: 用户名
            email: 用户邮箱
            workspace_id: 工作空间 ID
            expires_hours: Token 有效期（小时）
            
        Returns:
            JWT Token 字符串
        """
        payload = {
            "user_id": str(user_id),
            "username": username,
            "email": email,
            "workspace_id": workspace_id,
            "kiro_user": True,
            "iss": "kiro-platform",
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, self.shared_secret, algorithm="HS256")
        return token

    # ============== 用户管理相关 ==============

    async def sync_user(
        self,
        user_id: str,
        username: str,
        email: str = "",
        avatar_url: str = ""
    ) -> Dict[str, Any]:
        """
        同步用户到 Coze
        
        首次访问时自动创建或更新 Coze 用户信息。
        
        Args:
            user_id: Kiro 用户 ID
            username: 用户名
            email: 邮箱
            avatar_url: 头像 URL
            
        Returns:
            Coze 用户信息
        """
        client = await self._get_client()
        try:
            response = await client.post(
                "/api/v1/users/sync",
                json={
                    "external_user_id": str(user_id),
                    "username": username,
                    "email": email,
                    "avatar_url": avatar_url,
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to sync user to Coze: {e}")
            raise

    # ============== 工作空间相关 ==============

    async def create_workspace(
        self,
        name: str,
        description: str = "",
        owner_id: str = ""
    ) -> Dict[str, Any]:
        """
        创建工作空间
        
        Args:
            name: 工作空间名称
            description: 描述
            owner_id: 所有者用户 ID
            
        Returns:
            工作空间信息
        """
        client = await self._get_client()
        try:
            response = await client.post(
                "/api/v1/workspaces",
                json={
                    "name": name,
                    "description": description,
                    "owner_id": owner_id,
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create workspace in Coze: {e}")
            raise

    async def list_workspaces(self, user_id: str = "") -> List[Dict[str, Any]]:
        """获取工作空间列表"""
        client = await self._get_client()
        try:
            params = {}
            if user_id:
                params["user_id"] = user_id
            response = await client.get("/api/v1/workspaces", params=params)
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list workspaces from Coze: {e}")
            raise

    # ============== Agent 对话相关 ==============

    async def create_conversation(
        self,
        agent_id: str,
        query: str,
        user_id: str = "",
        conversation_id: str = "",
        additional_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建对话（非流式）
        
        Args:
            agent_id: Agent ID
            query: 用户问题
            user_id: 用户 ID
            conversation_id: 会话 ID（续传时使用）
            additional_variables: 附加变量
            
        Returns:
            对话结果
        """
        client = await self._get_client()
        try:
            payload = {
                "agent_id": agent_id,
                "query": query,
                "user_id": user_id,
            }
            if conversation_id:
                payload["conversation_id"] = conversation_id
            if additional_variables:
                payload["additional_variables"] = additional_variables

            response = await client.post(
                "/api/v1/agent/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create conversation in Coze: {e}")
            raise

    async def create_conversation_stream(
        self,
        agent_id: str,
        query: str,
        user_id: str = "",
        conversation_id: str = "",
        additional_variables: Optional[Dict[str, Any]] = None
    ):
        """
        创建流式对话
        
        返回一个异步生成器，用于 SSE 流式输出。
        
        Args:
            agent_id: Agent ID
            query: 用户问题
            user_id: 用户 ID
            conversation_id: 会话 ID
            additional_variables: 附加变量
            
        Yields:
            SSE 事件数据
        """
        client = await self._get_client()
        payload = {
            "agent_id": agent_id,
            "query": query,
            "user_id": user_id,
            "stream": True,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if additional_variables:
            payload["additional_variables"] = additional_variables

        try:
            async with client.stream(
                "POST",
                "/api/v1/agent/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            yield {"content": data}
        except httpx.HTTPError as e:
            logger.error(f"Failed to create stream conversation in Coze: {e}")
            raise

    # ============== 知识库相关 ==============

    async def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        workspace_id: str = ""
    ) -> Dict[str, Any]:
        """创建知识库"""
        client = await self._get_client()
        try:
            response = await client.post(
                "/api/v1/knowledge",
                json={
                    "name": name,
                    "description": description,
                    "workspace_id": workspace_id,
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create knowledge base in Coze: {e}")
            raise

    async def upload_document(
        self,
        knowledge_id: str,
        title: str,
        content: str = "",
        document_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        上传文档到知识库
        
        Args:
            knowledge_id: 知识库 ID
            title: 文档标题
            content: 文档内容
            document_type: 文档类型（text/file）
            metadata: 元数据
            
        Returns:
            文档信息
        """
        client = await self._get_client()
        try:
            response = await client.post(
                f"/api/v1/knowledge/{knowledge_id}/documents",
                json={
                    "title": title,
                    "content": content,
                    "document_type": document_type,
                    "metadata": metadata or {},
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to upload document to Coze knowledge base: {e}")
            raise

    async def search_knowledge(
        self,
        knowledge_id: str,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """搜索知识库"""
        client = await self._get_client()
        try:
            response = await client.post(
                f"/api/v1/knowledge/{knowledge_id}/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to search knowledge in Coze: {e}")
            raise

    async def delete_document(
        self,
        knowledge_id: str,
        document_id: str
    ) -> bool:
        """删除知识库文档"""
        client = await self._get_client()
        try:
            response = await client.delete(
                f"/api/v1/knowledge/{knowledge_id}/documents/{document_id}"
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete document from Coze: {e}")
            raise

    # ============== 工作流相关 ==============

    async def run_workflow(
        self,
        workflow_id: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: str = ""
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流 ID
            params: 工作流参数
            user_id: 用户 ID
            
        Returns:
            工作流执行结果
        """
        client = await self._get_client()
        try:
            response = await client.post(
                f"/api/v1/workflows/{workflow_id}/run",
                json={
                    "params": params or {},
                    "user_id": user_id,
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to run workflow in Coze: {e}")
            raise

    async def get_workflow_status(
        self,
        workflow_id: str,
        run_id: str
    ) -> Dict[str, Any]:
        """获取工作流执行状态"""
        client = await self._get_client()
        try:
            response = await client.get(
                f"/api/v1/workflows/{workflow_id}/runs/{run_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get workflow status from Coze: {e}")
            raise

    # ============== 插件相关 ==============

    async def list_plugins(
        self,
        workspace_id: str = "",
        category: str = ""
    ) -> List[Dict[str, Any]]:
        """获取插件列表"""
        client = await self._get_client()
        try:
            params = {}
            if workspace_id:
                params["workspace_id"] = workspace_id
            if category:
                params["category"] = category
            response = await client.get("/api/v1/plugins", params=params)
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list plugins from Coze: {e}")
            raise

    async def install_plugin(
        self,
        plugin_id: str,
        workspace_id: str = ""
    ) -> Dict[str, Any]:
        """安装插件到工作空间"""
        client = await self._get_client()
        try:
            response = await client.post(
                f"/api/v1/plugins/{plugin_id}/install",
                json={"workspace_id": workspace_id}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to install plugin in Coze: {e}")
            raise

    # ============== 健康检查 ==============

    async def health_check(self) -> bool:
        """
        检查 Coze 服务是否可用"""
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Coze health check failed: {e}")
            return False

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局单例
_coze_client: Optional[CozeClient] = None


def get_coze_client() -> CozeClient:
    """获取 Coze 客户端单例"""
    global _coze_client
    if _coze_client is None:
        _coze_client = CozeClient()
    return _coze_client


__all__ = [
    "CozeClient",
    "get_coze_client",
]
