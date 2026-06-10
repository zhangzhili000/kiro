import uuid
from sqlalchemy import Column, Text, JSON, TIMESTAMP, ForeignKey, Integer, LargeBinary, String
from datetime import datetime
from kiro.core.timezone_utils import get_beijing_time
from kiro.core.database import Base


class DocumentVector(Base):
    """文档向量表"""
    __tablename__ = "document_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_content = Column(Text, nullable=False)
    chunk_summary = Column(Text)
    keywords = Column(JSON)
    vector_data = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP, default=get_beijing_time, nullable=False)
    
    def __repr__(self):
        return f"<DocumentVector(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class AIConversation(Base):
    """AI对话记录表"""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_uuid = Column(String(36), index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # 添加索引
    title = Column(String(255))  # 对话标题
    question = Column(Text, nullable=False)
    question_analysis = Column(Text)  # 问题分析结果
    answer = Column(Text)  # 允许为空，用于存储"待处理"状态的对话
    status = Column(String(20), default="pending")  # pending, completed, error
    referenced_docs = Column(JSON)
    model = Column(String(100))
    tokens = Column(Integer, default=0)
    question_time = Column(TIMESTAMP, default=get_beijing_time, nullable=False)
    answer_time = Column(TIMESTAMP)
    duration = Column(Integer, default=0)
    processing_steps = Column(JSON)  # 存储处理步骤信息
    conversation_mode = Column(String(20), default="fast_qa")  # 对话模式：fast_qa, multi_round
    history_summary = Column(Text)  # 历史对话压缩摘要（用于多轮对话）
    created_at = Column(TIMESTAMP, default=get_beijing_time, nullable=False, index=True)  # 添加索引

    def __repr__(self):
        return f"<AIConversation(id={self.id}, uuid={self.conversation_uuid}, user_id={self.user_id})>"


class AIConfig(Base):
    """AI配置表"""
    __tablename__ = "ai_config"
    
    id = Column(Integer, primary_key=True, index=True)
    role_definition = Column(JSON, nullable=False)  # 角色定义：{name, description, guidelines}
    rules = Column(JSON, nullable=False)  # 规则配置：{answerStrategy, maxAnswerLength, citeSources, temperature, domains}
    created_at = Column(TIMESTAMP, default=get_beijing_time, nullable=False)
    updated_at = Column(TIMESTAMP, default=get_beijing_time, onupdate=get_beijing_time, nullable=False)
    
    def __repr__(self):
        return f"<AIConfig(id={self.id})>"


class PromptTemplate(Base):
    """提示词模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # role, rule, format, other
    description = Column(Text)
    content = Column(Text, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, default=get_beijing_time, nullable=False)
    updated_at = Column(TIMESTAMP, default=get_beijing_time, onupdate=get_beijing_time, nullable=False)
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name={self.name}, type={self.type})>"


class ModelConfig(Base):
    """AI模型配置表"""
    __tablename__ = "model_config"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # chat, embedding, rerank, document, image
    api_type = Column(String(50), nullable=False)  # alibaba_duilian, deepseek, openai, zhipu, siliconflow, custom
    model_id = Column(String(255), nullable=False)  # 模型标识
    api_key = Column(String(500), nullable=False)  # API密钥
    api_base = Column(String(500))  # API端点地址
    description = Column(Text)
    status = Column(String(20), default="active")  # active, disabled
    created_at = Column(TIMESTAMP, default=get_beijing_time, nullable=False)
    updated_at = Column(TIMESTAMP, default=get_beijing_time, onupdate=get_beijing_time, nullable=False)
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, type={self.type}, api_type={self.api_type}, model_id={self.model_id})>"
