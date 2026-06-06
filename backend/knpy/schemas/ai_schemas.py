from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class StreamEventType(str, Enum):
    """流式事件类型"""
    STEP = "step"
    SEARCH_RESULT = "search_result"
    CONTENT = "content"
    QUESTION_ANALYSIS = "question_analysis"
    DONE = "done"
    ERROR = "error"


class StreamEvent(BaseModel):
    """流式事件基础模型"""
    type: StreamEventType
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StepEventData(BaseModel):
    """步骤事件数据"""
    step: int
    title: str
    description: str
    status: str = "in_progress"  # in_progress, completed, error
    model: Optional[str] = None  # 使用的模型名称
    tokens: Optional[int] = None  # 消耗的token数


class SearchResultItem(BaseModel):
    """搜索结果项"""
    document_id: str
    document_title: Optional[str]
    chunk_content: str
    distance: float
    chunk_index: int


class SearchResultEventData(BaseModel):
    """搜索结果事件数据"""
    results: List[SearchResultItem]


class ContentEventData(BaseModel):
    """内容事件数据"""
    content: str
    is_first: bool = False
    is_last: bool = False


class QuestionAnalysisEventData(BaseModel):
    """问题分析事件数据"""
    content: str
    is_complete: bool = False


class DocumentConvertRequest(BaseModel):
    """文档转换请求"""
    file_path: str = Field(..., description="文件路径")
    file_type: Optional[str] = Field(None, description="文件类型")


class DocumentConvertResponse(BaseModel):
    """文档转换响应"""
    success: bool
    content: str
    html_content: str
    metadata: Optional[Dict[str, Any]]
    file_type: str


class DocumentProcessRequest(BaseModel):
    """文档处理请求"""
    document_id: UUID = Field(..., description="文档ID")


class DocumentProcessResponse(BaseModel):
    """文档处理响应"""
    success: bool
    document_id: UUID
    chunks_count: int
    summary: Optional[str]
    keywords: Optional[List[str]]


class DocumentSummaryResponse(BaseModel):
    """文档摘要响应"""
    document_id: UUID
    summary: str


class DocumentKeywordsResponse(BaseModel):
    """文档关键词响应"""
    document_id: UUID
    keywords: List[str]


class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(5, description="返回数量")


class VectorSearchResult(BaseModel):
    """向量搜索结果项"""
    document_id: str
    document_title: Optional[str]
    chunk_content: str
    distance: float
    chunk_index: int


class VectorSearchResponse(BaseModel):
    """向量搜索响应"""
    results: List[VectorSearchResult]


class ChatRequest(BaseModel):
    """AI对话请求"""
    question: str = Field(..., description="用户问题")
    use_context: bool = Field(True, description="是否使用文档上下文")
    conversation_uuid: Optional[str] = Field(None, description="对话UUID，用于多轮对话")
    conversation_mode: str = Field("fast_qa", description="对话模式：fast_qa-快速问答，multi_round-多轮对话")


class ChatResponse(BaseModel):
    """AI对话响应"""
    answer: str
    referenced_docs: Optional[List[Dict[str, Any]]]
    model: str
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    """对话历史响应"""
    id: int
    conversation_uuid: Optional[str] = None
    title: Optional[str] = None
    question: str
    question_analysis: Optional[str] = None
    answer: Optional[str] = None
    model: Optional[str] = None
    tokens: Optional[int] = None
    question_time: datetime
    answer_time: Optional[datetime] = None
    duration: Optional[int] = None
    processing_steps: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = "completed"  # pending, completed, error
    created_at: datetime


class UpdateConversationTitleRequest(BaseModel):
    """更新对话标题请求"""
    conversation_uuid: str = Field(..., description="对话UUID")
    title: str = Field(..., description="新的对话标题", max_length=255)


class UpdateConversationTitleResponse(BaseModel):
    """更新对话标题响应"""
    success: bool
    conversation_uuid: str
    title: str


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationHistoryResponse]


# AI配置管理相关schemas

class RoleDefinition(BaseModel):
    """角色定义"""
    name: str = Field("", description="角色名称")
    description: str = Field("", description="角色描述")
    guidelines: str = Field("", description="行为准则")


class AIRules(BaseModel):
    """AI规则配置"""
    answerStrategy: str = Field("hybrid", description="回答策略：knowledge_base, rule_based, hybrid")
    maxAnswerLength: int = Field(2000, description="最大回答长度")
    citeSources: bool = Field(True, description="是否引用来源")
    temperature: float = Field(0.7, description="温度系数")
    domains: List[str] = Field([], description="专业领域")


class PromptTemplateCreate(BaseModel):
    """提示词模板创建请求"""
    name: str = Field(..., description="模板名称", max_length=255)
    type: str = Field(..., description="模板类型：role, rule, format, other")
    description: str = Field("", description="模板描述")
    content: str = Field(..., description="模板内容")


class PromptTemplateUpdate(BaseModel):
    """提示词模板更新请求"""
    name: Optional[str] = Field(None, description="模板名称", max_length=255)
    type: Optional[str] = Field(None, description="模板类型")
    description: Optional[str] = Field(None, description="模板描述")
    content: Optional[str] = Field(None, description="模板内容")


class PromptTemplateResponse(BaseModel):
    """提示词模板响应"""
    id: int
    name: str
    type: str
    description: str
    content: str
    created_at: datetime
    updated_at: datetime


class AIConfigResponse(BaseModel):
    """AI配置响应"""
    roleDefinition: RoleDefinition
    rules: AIRules
    promptTemplates: List[PromptTemplateResponse]
