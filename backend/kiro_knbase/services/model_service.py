"""模型配置服务 - 从数据库读取模型配置并调用相应的API"""
import json
import os
from typing import List, Dict, Optional, Any
from fastapi import HTTPException
import requests


class ResponseParser:
    """统一的API响应解析器，支持多种模型响应格式"""
    
    SUPPORTED_FORMATS = {
        "openai": {
            "embedding": ["data", 0, "embedding"],
            "usage": ["usage"],
            "chat_content": ["choices", 0, "message", "content"],
            "chat_stream_content": ["choices", 0, "delta", "content"],
            "chat_usage": ["usage"]
        },
        "dashscope": {
            "embedding": ["output", "embeddings", 0, "embedding"],
            "usage": ["output", "usage"],
            "chat_content": ["output", "choices", 0, "message", "content", 0, "text"],
            "chat_stream_content": ["output", "choices", 0, "message", "content", 0, "text"],
            "chat_usage": ["output", "usage"]
        },
        "zhipu": {
            "embedding": ["data", 0, "embedding"],
            "usage": ["usage"],
            "chat_content": ["choices", 0, "message", "content"],
            "chat_stream_content": ["choices", 0, "delta", "content"],
            "chat_usage": ["usage"]
        },
        "siliconflow": {
            "embedding": ["data", 0, "embedding"],
            "usage": ["usage"],
            "chat_content": ["choices", 0, "message", "content"],
            "chat_stream_content": ["choices", 0, "delta", "content"],
            "chat_usage": ["usage"]
        },
        "deepseek": {
            "embedding": ["data", 0, "embedding"],
            "usage": ["usage"],
            "chat_content": ["choices", 0, "message", "content"],
            "chat_stream_content": ["choices", 0, "delta", "content"],
            "chat_usage": ["usage"]
        },
        "custom": {
            "embedding": ["data", 0, "embedding"],
            "usage": ["usage"],
            "chat_content": ["choices", 0, "message", "content"],
            "chat_stream_content": ["choices", 0, "delta", "content"],
            "chat_usage": ["usage"]
        }
    }
    
    def __init__(self, response_format: str = "openai"):
        """初始化解析器
        :param response_format: 响应格式类型，如 'openai', 'dashscope', 'zhipu', 'siliconflow', 'deepseek', 'custom'
        """
        self.format = response_format
        self.paths = self.SUPPORTED_FORMATS.get(response_format, self.SUPPORTED_FORMATS["openai"])
    
    def _get_value(self, data: Any, path: List[Any], default: Any = None) -> Any:
        """根据路径从嵌套数据中获取值
        :param data: 原始数据（dict或object）
        :param path: 路径列表，支持整数（列表索引）和字符串（字典键/对象属性）
        :param default: 默认值
        """
        try:
            current = data
            for key in path:
                if current is None:
                    return default
                if isinstance(current, dict):
                    if key not in current:
                        return default
                    current = current[key]
                elif isinstance(current, list):
                    if isinstance(key, int) and 0 <= key < len(current):
                        current = current[key]
                    else:
                        return default
                elif hasattr(current, key):
                    current = getattr(current, key)
                else:
                    return default
            return current
        except Exception:
            return default
    
    def parse_embedding(self, response: Any) -> dict:
        """解析embedding响应
        :param response: 原始响应（dict或object）
        :return: {"embedding": List[float], "usage": dict}
        """
        embedding = self._get_value(response, self.paths.get("embedding", ["data", 0, "embedding"]), [])
        
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], (int, float)):
            embedding = [float(x) for x in embedding]
        elif isinstance(embedding, list) and len(embedding) == 0:
            embedding = []
        else:
            print(f"Warning: Invalid embedding format, got: {type(embedding)}")
            embedding = []
        
        usage_data = self._get_value(response, self.paths.get("usage", ["usage"]), {})
        usage_info = {
            "prompt_tokens": usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0)
        }
        
        return {
            "embedding": embedding,
            "usage": usage_info
        }
    
    def parse_chat_completion(self, response: Any) -> dict:
        """解析聊天完成响应
        :param response: 原始响应（dict或object）
        :return: {"content": str, "usage": dict}
        """
        content = self._get_value(response, self.paths.get("chat_content", ["choices", 0, "message", "content"]), "")
        
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                content = content[0]["text"]
            elif isinstance(content[0], str):
                content = content[0]
            else:
                content = str(content)
        
        usage_data = self._get_value(response, self.paths.get("chat_usage", ["usage"]), {})
        usage_info = {
            "prompt_tokens": usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0)
        }
        
        return {
            "content": str(content).strip(),
            "usage": usage_info
        }
    
    def parse_chat_stream_chunk(self, chunk: Any) -> Optional[str]:
        """解析流式聊天响应的单个chunk
        :param chunk: 单个chunk（dict或object）
        :return: 文本内容，如果是结束信号则返回None
        """
        content = self._get_value(chunk, self.paths.get("chat_stream_content", ["choices", 0, "delta", "content"]), None)
        
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                content = content[0]["text"]
            elif isinstance(content[0], str):
                content = content[0]
        
        return str(content) if content else None
    
    @classmethod
    def detect_format(cls, api_type: str) -> str:
        """根据api_type自动检测响应格式
        :param api_type: API类型
        :return: 响应格式类型
        """
        format_mapping = {
            "alibaba_duilian": "dashscope",
            "deepseek": "deepseek",
            "openai": "openai",
            "zhipu": "zhipu",
            "siliconflow": "siliconflow",
            "custom": "custom"
        }
        return format_mapping.get(api_type, "openai")


class ModelConfigService:
    """模型配置服务 - 管理和获取模型配置"""
    
    def __init__(self, db):
        self.db = db
        self.config_cache = {}
        self._load_configs()
    
    def _load_configs(self):
        """从数据库加载所有模型配置"""
        from kiro_knbase.models.ai_models import ModelConfig
        
        try:
            configs = self.db.query(ModelConfig).filter(ModelConfig.status == "active").all()
            for config in configs:
                key = f"{config.type}_{config.id}"
                self.config_cache[key] = {
                    "id": config.id,
                    "type": config.type,
                    "api_type": config.api_type,
                    "model_id": config.model_id,
                    "api_key": config.api_key,
                    "api_base": config.api_base,
                    "description": config.description
                }
        except Exception as e:
            print(f"Failed to load model configs: {e}")
    
    def get_active_config(self, model_type: str) -> Optional[dict]:
        """获取指定类型的活跃模型配置"""
        # 优先返回缓存的配置
        for key, config in self.config_cache.items():
            if config["type"] == model_type:
                return config
        
        # 如果缓存中没有，从数据库查询
        from kiro_knbase.models.ai_models import ModelConfig
        
        try:
            config = self.db.query(ModelConfig).filter(
                ModelConfig.type == model_type,
                ModelConfig.status == "active"
            ).first()
            
            if config:
                result = {
                    "id": config.id,
                    "type": config.type,
                    "api_type": config.api_type,
                    "model_id": config.model_id,
                    "api_key": config.api_key,
                    "api_base": config.api_base,
                    "description": config.description
                }
                self.config_cache[f"{model_type}_{config.id}"] = result
                return result
        except Exception as e:
            print(f"Failed to get model config: {e}")
        
        return None
    
    def invalidate_cache(self):
        """清除配置缓存"""
        self.config_cache.clear()


class DynamicAIClient:
    """动态AI客户端 - 根据配置调用不同的模型API"""
    
    def __init__(self, db):
        self.db = db
        self.config_service = ModelConfigService(db)
        self.timeout = 300  # 5分钟超时
        self.prompt_templates = {}
        
    def set_prompt_templates(self, templates: Dict[str, str]):
        """设置提示词模板"""
        self.prompt_templates = templates
    
    def _get_client_for_model(self, model_type: str):
        """根据模型类型获取对应的客户端"""
        config = self.config_service.get_active_config(model_type)
        
        if not config:
            raise HTTPException(
                status_code=500, 
                detail=f"未配置有效的{self._get_model_type_name(model_type)}模型，请联系管理员"
            )
        
        api_type = config["api_type"]
        
        if api_type == "alibaba_duilian":
            return DashScopeClient(config)
        elif api_type == "deepseek":
            return DeepSeekClient(config)
        elif api_type == "openai":
            return OpenAIClient(config)
        elif api_type == "zhipu":
            return ZhiPuClient(config)
        elif api_type == "siliconflow":
            return SiliconFlowClient(config)
        elif api_type == "custom":
            return CustomAPIClient(config)
        else:
            raise HTTPException(status_code=500, detail=f"不支持的API类型: {api_type}")
    
    def _get_model_type_name(self, model_type: str) -> str:
        """获取模型类型中文名"""
        type_names = {
            "chat": "智能对话",
            "embedding": "向量",
            "rerank": "重排序",
            "document": "文档分析",
            "image": "图像分析"
        }
        return type_names.get(model_type, model_type)
    
    def get_embedding(self, text: str) -> dict:
        """获取文本向量，返回包含embedding和usage的字典"""
        client = self._get_client_for_model("embedding")
        return client.get_embedding(text)
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        """获取文本摘要"""
        client = self._get_client_for_model("chat")
        return client.get_summary(text, max_length)
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        """流式获取文本摘要"""
        client = self._get_client_for_model("chat")
        return client.get_summary_stream(text, max_length)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        client = self._get_client_for_model("chat")
        return client.extract_keywords(text, top_k)
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        """流式提取关键词"""
        client = self._get_client_for_model("chat")
        return client.extract_keywords_stream(text, top_k)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        """AI对话完成"""
        client = self._get_client_for_model("chat")
        client.set_prompt_templates(self.prompt_templates)
        return client.chat_completion(prompt, context, answer_strategy)
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        """流式AI对话完成"""
        client = self._get_client_for_model("chat")
        client.set_prompt_templates(self.prompt_templates)
        return client.chat_completion_stream(prompt, context, answer_strategy)
    
    def analyze_question(self, question: str) -> str:
        """分析用户问题"""
        client = self._get_client_for_model("chat")
        return client.analyze_question(question)
    
    def analyze_question_detailed(self, question: str, context: str = "") -> dict:
        """详细分析用户问题"""
        client = self._get_client_for_model("chat")
        return client.analyze_question_detailed(question, context)
    
    def analyze_question_stream(self, question: str):
        """流式分析用户问题"""
        client = self._get_client_for_model("chat")
        return client.analyze_question_stream(question)
    
    def quick_analyze_question(self, question: str) -> dict:
        """快速分析用户问题（基于关键词，毫秒级）"""
        client = self._get_client_for_model("chat")
        return client._default_analysis(question)
    
    def compress_conversation_history(self, history: List[Dict[str, str]], max_length: int = 500) -> Dict[str, Any]:
        """
        压缩对话历史，使用LLM进行摘要
        :param history: 历史对话列表，每个元素包含 'question' 和 'answer'
        :param max_length: 最大摘要长度
        :return: 包含压缩后的摘要和token使用量的字典
        """
        if not history:
            return {"summary": "", "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        
        # 构建历史对话文本
        history_text = ""
        for i, item in enumerate(history):
            history_text += f"对话{i+1}：\n用户：{item.get('question', '')}\n助手：{item.get('answer', '')}\n\n"
        
        # 构建压缩提示词
        prompt = f"""
请对以下对话历史进行压缩摘要，保留关键信息和上下文，用于后续对话参考：

{history_text}

请用不超过{max_length}字总结以上对话的核心内容、讨论要点和关键结论：
"""
        
        client = self._get_client_for_model("chat")
        result = client._call_completion(prompt, max_length, 0.3)
        
        return {
            "summary": result["content"],
            "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        }


class BaseAIClient:
    """AI客户端基类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model_id = config["model_id"]
        self.api_key = config["api_key"]
        self.api_base = config["api_base"]
        self.timeout = 300
        self.prompt_templates = {}
        # 创建响应解析器
        self.api_type = config.get("api_type", "openai")
        self.response_parser = ResponseParser(ResponseParser.detect_format(self.api_type))
    
    def set_prompt_templates(self, templates: Dict[str, str]):
        """设置提示词模板"""
        self.prompt_templates = templates
    
    def get_embedding(self, text: str) -> dict:
        raise NotImplementedError
    
    def _parse_embedding_response(self, response: Any) -> dict:
        """解析embedding响应（使用统一解析器）"""
        return self.response_parser.parse_embedding(response)
    
    def _parse_chat_response(self, response: Any) -> dict:
        """解析聊天响应（使用统一解析器）"""
        return self.response_parser.parse_chat_completion(response)
    
    def _parse_chat_stream_chunk(self, chunk: Any) -> Optional[str]:
        """解析流式聊天响应的单个chunk（使用统一解析器）"""
        return self.response_parser.parse_chat_stream_chunk(chunk)
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        raise NotImplementedError
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        raise NotImplementedError
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        raise NotImplementedError
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        raise NotImplementedError
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        raise NotImplementedError
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        raise NotImplementedError
    
    def analyze_question(self, question: str) -> str:
        raise NotImplementedError
    
    def analyze_question_detailed(self, question: str, context: str = "") -> dict:
        raise NotImplementedError
    
    def analyze_question_stream(self, question: str):
        raise NotImplementedError
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> str:
        """构建完整的提示词"""
        role_template = self.prompt_templates.get("role", "")
        strategy_template = ""
        
        if answer_strategy == "knowledge_base":
            strategy_template = self.prompt_templates.get("knowledge_base_rule", "")
        elif answer_strategy == "rule_based":
            strategy_template = self.prompt_templates.get("rule_based_rule", "")
        else:
            kb_rule = self.prompt_templates.get("knowledge_base_rule", "")
            rule_rule = self.prompt_templates.get("rule_based_rule", "")
            strategy_template = f"{kb_rule}\n\n{rule_rule}"
        
        format_template = self.prompt_templates.get("format", "")
        
        parts = []
        if role_template:
            parts.append(f"角色定义：\n{role_template}")
        if strategy_template:
            parts.append(f"回答规则：\n{strategy_template}")
        if format_template:
            parts.append(f"格式要求：\n{format_template}")
        if context:
            parts.append(f"参考文档：\n{context}")
        parts.append(f"问题：{prompt}")
        parts.append("请根据上述信息回答问题。")
        
        return "\n\n".join(parts)


class DashScopeClient(BaseAIClient):
    """阿里百炼API客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import dashscope
            self.dashscope = dashscope
            self.dashscope.api_key = self.api_key
            if self.api_base:
                self.dashscope.base_http_api_url = self.api_base
        except ImportError:
            raise HTTPException(status_code=500, detail="未安装dashscope依赖")
    
    def get_embedding(self, text: str) -> dict:
        try:
            input_data = [{'text': text}]
            response = self.dashscope.MultiModalEmbedding.call(
                model=self.model_id,
                input=input_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = self._parse_embedding_response(response)
                # 如果API没有返回token使用量，进行估算
                if result["usage"]["total_tokens"] == 0:
                    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                    other_chars = len(text) - chinese_chars
                    estimated_tokens = (chinese_chars // 2) + (other_chars // 4)
                    result["usage"] = {
                        "prompt_tokens": estimated_tokens,
                        "completion_tokens": 0,
                        "total_tokens": estimated_tokens
                    }
                return result
            else:
                raise HTTPException(status_code=500, detail=f"Embedding API error: {response.message}")
        except HTTPException:
            raise
        except Exception as e:
            print(f"DashScope embedding error: {e}")
            raise HTTPException(status_code=500, detail="向量生成失败，请稍后重试")
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        result = self._call_completion(prompt, max_length, 0.3)
        return result["content"]
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        return self._call_completion_stream(prompt, max_length, 0.3)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        result = self._call_completion(prompt, 100, 0.1)
        content = result["content"]
        keywords = [k.strip() for k in content.split("，") if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in content.split(",") if k.strip()]
        return keywords[:top_k]
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        return self._call_completion_stream(prompt, 100, 0.1)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        result = self._call_completion(full_prompt, 1000, 0.7)
        return {"answer": result["content"].strip(), "model": self.model_id, "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})}
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        return self._call_completion_stream(full_prompt, 1000, 0.7)
    
    def analyze_question(self, question: str) -> str:
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion(prompt, 200, 0.5)
    
    def analyze_question_detailed(self, question: str, context: str = "") -> dict:
        # 如果有上下文（历史对话摘要），将其添加到提示词中
        context_prompt = ""
        if context:
            context_prompt = f"""
历史对话摘要：
{context}

"""
        
        prompt = f"""请分析以下用户问题，并返回JSON格式的分析结果：

{context_prompt}用户问题：{question}

分析规则：
1. 如果问题包含多个子问题，只要有一个子问题需要知识库回答，needs_knowledge_base就为true
2. 关于概念定义、专业术语解释、事实性知识查询的问题通常需要知识库
3. 关于系统功能、使用方法、自我介绍的问题属于系统问题
4. 日常问候、闲聊类问题不需要知识库
5. 如果有历史对话上下文，需要结合上下文理解当前问题的意图
6. 上下文相关的问题（如"具体应该怎么做"、"还有吗"、"详细说说"等）需要参考之前的对话内容来判断是否需要知识库

分析维度：
1. question_type: 问题类型，如"知识性"、"查询性"、"建议性"、"系统问题"、"闲聊"等
2. core_requirement: 核心需求，用一句话概括
3. needs_knowledge_base: 是否需要基于知识库回答，true或false
4. is_system_question: 是否是关于系统本身的问题，true或false
5. suggested_strategy: 建议的回答策略，可选值："knowledge_base"、"system_info"、"direct_answer"、"hybrid"

请仅返回JSON格式，不要包含其他内容。"""
        
        result = self._call_completion(prompt, 300, 0.3)
        try:
            analysis_data = json.loads(result["content"].strip())
            # 添加token使用量信息
            analysis_data["_usage"] = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return analysis_data
        except json.JSONDecodeError:
            default_result = self._default_analysis(question)
            default_result["_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return default_result
    
    def analyze_question_stream(self, question: str):
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion_stream(prompt, 200, 0.5)
    
    def _call_completion(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        try:
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            response = self.dashscope.MultiModalConversation.call(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content[0]["text"]
                # 获取token使用量
                usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                # 检查response.usage
                if hasattr(response, 'usage') and response.usage:
                    usage_info = {
                        "prompt_tokens": getattr(response.usage, 'input_tokens', 0) or getattr(response.usage, 'prompt_tokens', 0),
                        "completion_tokens": getattr(response.usage, 'output_tokens', 0) or getattr(response.usage, 'completion_tokens', 0),
                        "total_tokens": getattr(response.usage, 'total_tokens', 0)
                    }
                # 检查response.output.usage
                elif hasattr(response.output, 'usage') and response.output.usage:
                    usage_info = {
                        "prompt_tokens": getattr(response.output.usage, 'input_tokens', 0) or getattr(response.output.usage, 'prompt_tokens', 0),
                        "completion_tokens": getattr(response.output.usage, 'output_tokens', 0) or getattr(response.output.usage, 'completion_tokens', 0),
                        "total_tokens": getattr(response.output.usage, 'total_tokens', 0)
                    }
                # 尝试从response.headers获取（某些API会在headers中返回）
                elif hasattr(response, 'headers') and response.headers:
                    pass  # headers中通常不包含usage信息
                return {
                    "content": content.strip(),
                    "usage": usage_info
                }
            else:
                raise HTTPException(status_code=500, detail=f"API error: {response.message}")
        except HTTPException:
            raise
        except Exception as e:
            print(f"DashScope completion error: {e}")
            raise HTTPException(status_code=500, detail="AI调用失败，请稍后重试")
    
    def _call_completion_stream(self, prompt: str, max_tokens: int, temperature: float):
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            response = self.dashscope.MultiModalConversation.call(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout,
                stream=True
            )
            
            first_chunk = True
            for chunk in response:
                if chunk.status_code == 200:
                    # 检查是否有usage信息（通常在最后一个chunk中）
                    if hasattr(chunk, 'usage') and chunk.usage:
                        usage_info = {
                            "prompt_tokens": getattr(chunk.usage, 'input_tokens', 0) or getattr(chunk.usage, 'prompt_tokens', 0),
                            "completion_tokens": getattr(chunk.usage, 'output_tokens', 0) or getattr(chunk.usage, 'completion_tokens', 0),
                            "total_tokens": getattr(chunk.usage, 'total_tokens', 0)
                        }
                    # 检查output.usage
                    elif hasattr(chunk, 'output') and chunk.output and hasattr(chunk.output, 'usage') and chunk.output.usage:
                        usage_info = {
                            "prompt_tokens": getattr(chunk.output.usage, 'input_tokens', 0) or getattr(chunk.output.usage, 'prompt_tokens', 0),
                            "completion_tokens": getattr(chunk.output.usage, 'output_tokens', 0) or getattr(chunk.output.usage, 'completion_tokens', 0),
                            "total_tokens": getattr(chunk.output.usage, 'total_tokens', 0)
                        }
                    if hasattr(chunk, 'output') and chunk.output:
                        if hasattr(chunk.output, 'choices') and chunk.output.choices:
                            choice = chunk.output.choices[0]
                            if hasattr(choice, 'message') and choice.message:
                                content = choice.message.content
                                if isinstance(content, list) and len(content) > 0:
                                    if isinstance(content[0], dict) and 'text' in content[0]:
                                        yield content[0]['text'], first_chunk, False, None
                                        first_chunk = False
                elif chunk.status_code != 200:
                    # 处理非200状态码
                    error_msg = getattr(chunk, 'message', 'API调用失败')
                    print(f"DashScope API error: {error_msg}")
                    raise HTTPException(status_code=500, detail=f"模型API调用失败: {error_msg}")
            yield "", False, True, usage_info
        except HTTPException:
            raise
        except Exception as e:
            print(f"DashScope stream error: {e}")
            # 根据错误类型提供更具体的错误信息
            error_str = str(e).lower()
            if "connection" in error_str or "network" in error_str:
                raise HTTPException(status_code=500, detail="无法连接到模型服务，请检查网络连接或模型配置的API地址是否正确")
            elif "timeout" in error_str:
                raise HTTPException(status_code=500, detail="模型服务响应超时，请稍后重试或检查模型配置")
            elif "auth" in error_str or "key" in error_str or "permission" in error_str:
                raise HTTPException(status_code=500, detail="模型API密钥无效或权限不足，请检查模型配置")
            else:
                raise HTTPException(status_code=500, detail="模型API调用失败，请检查模型配置或稍后重试")
    
    def _default_analysis(self, question: str) -> dict:
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        if not is_system_question:
            for keyword in chat_keywords:
                if keyword in lower_question:
                    needs_knowledge_base = False
                    question_type = "闲聊"
                    suggested_strategy = "direct_answer"
                    break
        
        return {
            "question_type": question_type,
            "core_requirement": question,
            "needs_knowledge_base": needs_knowledge_base,
            "is_system_question": is_system_question,
            "suggested_strategy": suggested_strategy
        }


class DeepSeekClient(BaseAIClient):
    """DeepSeek API客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = self.api_base if self.api_base else "https://api.deepseek.com/v1"
    
    def _request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API error: {e}")
            raise HTTPException(status_code=500, detail="API调用失败，请稍后重试")
    
    def get_embedding(self, text: str) -> dict:
        payload = {
            "model": self.model_id,
            "input": text
        }
        response = self._request("/embeddings", payload)
        embedding = response.get("data", [{}])[0].get("embedding", [])
        # 获取token使用量
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "embedding": embedding,
            "usage": usage_info
        }
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        result = self._call_completion(prompt, max_length, 0.3)
        return result["content"]
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        return self._call_completion_stream(prompt, max_length, 0.3)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        result = self._call_completion(prompt, 100, 0.1)
        content = result["content"]
        keywords = [k.strip() for k in content.split("，") if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in content.split(",") if k.strip()]
        return keywords[:top_k]
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        return self._call_completion_stream(prompt, 100, 0.1)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        result = self._call_completion(full_prompt, 1000, 0.7)
        return {"answer": result["content"].strip(), "model": self.model_id, "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})}
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        return self._call_completion_stream(full_prompt, 1000, 0.7)
    
    def analyze_question(self, question: str) -> str:
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion(prompt, 200, 0.5)
    
    def analyze_question_detailed(self, question: str, context: str = "") -> dict:
        # 如果有上下文（历史对话摘要），将其添加到提示词中
        context_prompt = ""
        if context:
            context_prompt = f"""
历史对话摘要：
{context}

"""
        
        prompt = f"""请分析以下用户问题，并返回JSON格式的分析结果：

{context_prompt}用户问题：{question}

分析规则：
1. 如果问题包含多个子问题，只要有一个子问题需要知识库回答，needs_knowledge_base就为true
2. 关于概念定义、专业术语解释、事实性知识查询的问题通常需要知识库
3. 关于系统功能、使用方法、自我介绍的问题属于系统问题
4. 日常问候、闲聊类问题不需要知识库
5. 如果有历史对话上下文，需要结合上下文理解当前问题的意图
6. 上下文相关的问题（如"具体应该怎么做"、"还有吗"、"详细说说"等）需要参考之前的对话内容来判断是否需要知识库

分析维度：
1. question_type: 问题类型，如"知识性"、"查询性"、"建议性"、"系统问题"、"闲聊"等
2. core_requirement: 核心需求，用一句话概括
3. needs_knowledge_base: 是否需要基于知识库回答，true或false
4. is_system_question: 是否是关于系统本身的问题，true或false
5. suggested_strategy: 建议的回答策略，可选值："knowledge_base"、"system_info"、"direct_answer"、"hybrid"

请仅返回JSON格式，不要包含其他内容。"""
        
        result = self._call_completion(prompt, 300, 0.3)
        try:
            analysis_data = json.loads(result["content"].strip())
            # 添加token使用量信息
            analysis_data["_usage"] = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return analysis_data
        except json.JSONDecodeError:
            default_result = self._default_analysis(question)
            default_result["_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return default_result
    
    def analyze_question_stream(self, question: str):
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion_stream(prompt, 200, 0.5)
    
    def _call_completion(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = self._request("/chat/completions", payload)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        # 获取token使用量
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "content": content,
            "usage": usage_info
        }
    
    def _call_completion_stream(self, prompt: str, max_tokens: int, temperature: float):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                first_chunk = True
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            if line == "[DONE]":
                                # 返回最后一个chunk，包含usage信息
                                yield "", False, True, usage_info
                                break
                            try:
                                data = json.loads(line)
                                # 检查API返回的错误
                                if "error" in data:
                                    error_msg = data["error"].get("message", "API调用失败")
                                    print(f"DeepSeek API error: {error_msg}")
                                    raise HTTPException(status_code=500, detail=f"模型API调用失败: {error_msg}")
                                # 检查是否有usage信息（某些API在最后一个chunk中返回）
                                if "usage" in data and data["usage"]:
                                    usage_info = data["usage"]
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content, first_chunk, False, None
                                    first_chunk = False
                            except json.JSONDecodeError:
                                pass
        except requests.exceptions.ConnectionError as e:
            print(f"DeepSeek connection error: {e}")
            raise HTTPException(status_code=500, detail="无法连接到模型服务，请检查网络连接或模型配置的API地址是否正确")
        except requests.exceptions.Timeout as e:
            print(f"DeepSeek timeout error: {e}")
            raise HTTPException(status_code=500, detail="模型服务响应超时，请稍后重试或检查模型配置")
        except requests.exceptions.HTTPError as e:
            print(f"DeepSeek HTTP error: {e}")
            status_code = e.response.status_code if e.response else 500
            if status_code == 401 or status_code == 403:
                raise HTTPException(status_code=500, detail="模型API密钥无效或权限不足，请检查模型配置")
            else:
                raise HTTPException(status_code=500, detail=f"模型服务返回错误 (HTTP {status_code})，请检查模型配置")
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek stream error: {e}")
            raise HTTPException(status_code=500, detail="模型API调用失败，请检查模型配置或稍后重试")
    
    def _default_analysis(self, question: str) -> dict:
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        if not is_system_question:
            for keyword in chat_keywords:
                if keyword in lower_question:
                    needs_knowledge_base = False
                    question_type = "闲聊"
                    suggested_strategy = "direct_answer"
                    break
        
        return {
            "question_type": question_type,
            "core_requirement": question,
            "needs_knowledge_base": needs_knowledge_base,
            "is_system_question": is_system_question,
            "suggested_strategy": suggested_strategy
        }


class OpenAIClient(BaseAIClient):
    """OpenAI API客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = self.api_base if self.api_base else "https://api.openai.com/v1"
    
    def _request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"OpenAI API error: {e}")
            raise HTTPException(status_code=500, detail="API调用失败，请稍后重试")
    
    def get_embedding(self, text: str) -> dict:
        payload = {
            "model": self.model_id,
            "input": text
        }
        response = self._request("/embeddings", payload)
        return self._parse_embedding_response(response)
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        result = self._call_completion(prompt, max_length, 0.3)
        return result["content"]
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        return self._call_completion_stream(prompt, max_length, 0.3)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        result = self._call_completion(prompt, 100, 0.1)
        content = result["content"]
        keywords = [k.strip() for k in content.split("，") if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in content.split(",") if k.strip()]
        return keywords[:top_k]
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        return self._call_completion_stream(prompt, 100, 0.1)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        result = self._call_completion(full_prompt, 1000, 0.7)
        return {"answer": result["content"].strip(), "model": self.model_id, "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})}
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        return self._call_completion_stream(full_prompt, 1000, 0.7)
    
    def analyze_question(self, question: str) -> str:
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion(prompt, 200, 0.5)
    
    def analyze_question_detailed(self, question: str) -> dict:
        prompt = f"""请分析以下用户问题，并返回JSON格式的分析结果：

用户问题：{question}

分析规则：
1. 如果问题包含多个子问题，只要有一个子问题需要知识库回答，needs_knowledge_base就为true
2. 关于概念定义、专业术语解释、事实性知识查询的问题通常需要知识库
3. 关于系统功能、使用方法、自我介绍的问题属于系统问题
4. 日常问候、闲聊类问题不需要知识库

分析维度：
1. question_type: 问题类型，如"知识性"、"查询性"、"建议性"、"系统问题"、"闲聊"等
2. core_requirement: 核心需求，用一句话概括
3. needs_knowledge_base: 是否需要基于知识库回答，true或false
4. is_system_question: 是否是关于系统本身的问题，true或false
5. suggested_strategy: 建议的回答策略，可选值："knowledge_base"、"system_info"、"direct_answer"、"hybrid"

请仅返回JSON格式，不要包含其他内容。"""
        
        result = self._call_completion(prompt, 300, 0.3)
        try:
            analysis_data = json.loads(result["content"].strip())
            analysis_data["_usage"] = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return analysis_data
        except json.JSONDecodeError:
            default_result = self._default_analysis(question)
            default_result["_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return default_result
    
    def analyze_question_stream(self, question: str):
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion_stream(prompt, 200, 0.5)
    
    def _call_completion(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = self._request("/chat/completions", payload)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "content": content,
            "usage": usage_info
        }
    
    def _call_completion_stream(self, prompt: str, max_tokens: int, temperature: float):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                first_chunk = True
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            if line == "[DONE]":
                                yield "", False, True, usage_info
                                break
                            try:
                                data = json.loads(line)
                                # 检查是否有usage信息
                                if "usage" in data and data["usage"]:
                                    usage_info = data["usage"]
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content, first_chunk, False, None
                                    first_chunk = False
                            except json.JSONDecodeError:
                                pass
        except requests.exceptions.RequestException as e:
            print(f"OpenAI stream error: {e}")
            raise HTTPException(status_code=500, detail="流式API调用失败，请稍后重试")
    
    def _default_analysis(self, question: str) -> dict:
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        if not is_system_question:
            for keyword in chat_keywords:
                if keyword in lower_question:
                    needs_knowledge_base = False
                    question_type = "闲聊"
                    suggested_strategy = "direct_answer"
                    break
        
        return {
            "question_type": question_type,
            "core_requirement": question,
            "needs_knowledge_base": needs_knowledge_base,
            "is_system_question": is_system_question,
            "suggested_strategy": suggested_strategy
        }


class ZhiPuClient(BaseAIClient):
    """智谱AI API客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = self.api_base if self.api_base else "https://open.bigmodel.cn/api/paas/v4"
    
    def _request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ZhiPu API error: {e}")
            raise HTTPException(status_code=500, detail="API调用失败，请稍后重试")
    
    def get_embedding(self, text: str) -> dict:
        payload = {
            "model": self.model_id,
            "input": [text]
        }
        response = self._request("/embeddings", payload)
        embedding = response.get("data", [{}])[0].get("embedding", [])
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "embedding": embedding,
            "usage": usage_info
        }
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        result = self._call_completion(prompt, max_length, 0.3)
        return result["content"]
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        return self._call_completion_stream(prompt, max_length, 0.3)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        result = self._call_completion(prompt, 100, 0.1)
        content = result["content"]
        keywords = [k.strip() for k in content.split("，") if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in content.split(",") if k.strip()]
        return keywords[:top_k]
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        return self._call_completion_stream(prompt, 100, 0.1)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        result = self._call_completion(full_prompt, 1000, 0.7)
        return {"answer": result["content"].strip(), "model": self.model_id, "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})}
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        return self._call_completion_stream(full_prompt, 1000, 0.7)
    
    def analyze_question(self, question: str) -> str:
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion(prompt, 200, 0.5)
    
    def analyze_question_detailed(self, question: str) -> dict:
        prompt = f"""请分析以下用户问题，并返回JSON格式的分析结果：

用户问题：{question}

分析规则：
1. 如果问题包含多个子问题，只要有一个子问题需要知识库回答，needs_knowledge_base就为true
2. 关于概念定义、专业术语解释、事实性知识查询的问题通常需要知识库
3. 关于系统功能、使用方法、自我介绍的问题属于系统问题
4. 日常问候、闲聊类问题不需要知识库

分析维度：
1. question_type: 问题类型，如"知识性"、"查询性"、"建议性"、"系统问题"、"闲聊"等
2. core_requirement: 核心需求，用一句话概括
3. needs_knowledge_base: 是否需要基于知识库回答，true或false
4. is_system_question: 是否是关于系统本身的问题，true或false
5. suggested_strategy: 建议的回答策略，可选值："knowledge_base"、"system_info"、"direct_answer"、"hybrid"

请仅返回JSON格式，不要包含其他内容。"""
        
        result = self._call_completion(prompt, 300, 0.3)
        try:
            analysis_data = json.loads(result["content"].strip())
            analysis_data["_usage"] = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return analysis_data
        except json.JSONDecodeError:
            default_result = self._default_analysis(question)
            default_result["_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return default_result
    
    def analyze_question_stream(self, question: str):
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion_stream(prompt, 200, 0.5)
    
    def _call_completion(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = self._request("/chat/completions", payload)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "content": content,
            "usage": usage_info
        }
    
    def _call_completion_stream(self, prompt: str, max_tokens: int, temperature: float):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                first_chunk = True
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            if line == "[DONE]":
                                yield "", False, True, usage_info
                                break
                            try:
                                data = json.loads(line)
                                if "usage" in data and data["usage"]:
                                    usage_info = data["usage"]
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content, first_chunk, False, None
                                    first_chunk = False
                            except json.JSONDecodeError:
                                pass
        except requests.exceptions.RequestException as e:
            print(f"ZhiPu stream error: {e}")
            raise HTTPException(status_code=500, detail="流式API调用失败，请稍后重试")
    
    def _default_analysis(self, question: str) -> dict:
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        if not is_system_question:
            for keyword in chat_keywords:
                if keyword in lower_question:
                    needs_knowledge_base = False
                    question_type = "闲聊"
                    suggested_strategy = "direct_answer"
                    break
        
        return {
            "question_type": question_type,
            "core_requirement": question,
            "needs_knowledge_base": needs_knowledge_base,
            "is_system_question": is_system_question,
            "suggested_strategy": suggested_strategy
        }


class SiliconFlowClient(BaseAIClient):
    """硅基流动API客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = self.api_base if self.api_base else "https://api.siliconflow.cn/v1"
    
    def _request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"SiliconFlow API error: {e}")
            raise HTTPException(status_code=500, detail="API调用失败，请稍后重试")
    
    def get_embedding(self, text: str) -> dict:
        payload = {
            "model": self.model_id,
            "input": text
        }
        response = self._request("/embeddings", payload)
        return self._parse_embedding_response(response)
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        result = self._call_completion(prompt, max_length, 0.3)
        return result["content"]
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        return self._call_completion_stream(prompt, max_length, 0.3)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        result = self._call_completion(prompt, 100, 0.1)
        content = result["content"]
        keywords = [k.strip() for k in content.split("，") if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in content.split(",") if k.strip()]
        return keywords[:top_k]
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        return self._call_completion_stream(prompt, 100, 0.1)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        result = self._call_completion(full_prompt, 1000, 0.7)
        return {"answer": result["content"].strip(), "model": self.model_id, "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})}
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        return self._call_completion_stream(full_prompt, 1000, 0.7)
    
    def analyze_question(self, question: str) -> str:
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion(prompt, 200, 0.5)
    
    def analyze_question_detailed(self, question: str) -> dict:
        prompt = f"""请分析以下用户问题，并返回JSON格式的分析结果：

用户问题：{question}

分析规则：
1. 如果问题包含多个子问题，只要有一个子问题需要知识库回答，needs_knowledge_base就为true
2. 关于概念定义、专业术语解释、事实性知识查询的问题通常需要知识库
3. 关于系统功能、使用方法、自我介绍的问题属于系统问题
4. 日常问候、闲聊类问题不需要知识库

分析维度：
1. question_type: 问题类型，如"知识性"、"查询性"、"建议性"、"系统问题"、"闲聊"等
2. core_requirement: 核心需求，用一句话概括
3. needs_knowledge_base: 是否需要基于知识库回答，true或false
4. is_system_question: 是否是关于系统本身的问题，true或false
5. suggested_strategy: 建议的回答策略，可选值："knowledge_base"、"system_info"、"direct_answer"、"hybrid"

请仅返回JSON格式，不要包含其他内容。"""
        
        result = self._call_completion(prompt, 300, 0.3)
        try:
            analysis_data = json.loads(result["content"].strip())
            analysis_data["_usage"] = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return analysis_data
        except json.JSONDecodeError:
            default_result = self._default_analysis(question)
            default_result["_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return default_result
    
    def analyze_question_stream(self, question: str):
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion_stream(prompt, 200, 0.5)
    
    def _call_completion(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = self._request("/chat/completions", payload)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "content": content,
            "usage": usage_info
        }
    
    def _call_completion_stream(self, prompt: str, max_tokens: int, temperature: float):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                first_chunk = True
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            if line == "[DONE]":
                                yield "", False, True, usage_info
                                break
                            try:
                                data = json.loads(line)
                                if "usage" in data and data["usage"]:
                                    usage_info = data["usage"]
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content, first_chunk, False, None
                                    first_chunk = False
                            except json.JSONDecodeError:
                                pass
        except requests.exceptions.RequestException as e:
            print(f"SiliconFlow stream error: {e}")
            raise HTTPException(status_code=500, detail="流式API调用失败，请稍后重试")
    
    def _default_analysis(self, question: str) -> dict:
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        if not is_system_question:
            for keyword in chat_keywords:
                if keyword in lower_question:
                    needs_knowledge_base = False
                    question_type = "闲聊"
                    suggested_strategy = "direct_answer"
                    break
        
        return {
            "question_type": question_type,
            "core_requirement": question,
            "needs_knowledge_base": needs_knowledge_base,
            "is_system_question": is_system_question,
            "suggested_strategy": suggested_strategy
        }


class CustomAPIClient(BaseAIClient):
    """自定义API客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        if not self.api_base:
            raise HTTPException(status_code=500, detail="自定义API需要配置API端点")
    
    def _request(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Custom API error: {e}")
            raise HTTPException(status_code=500, detail="API调用失败，请稍后重试")
    
    def get_embedding(self, text: str) -> dict:
        payload = {
            "model": self.model_id,
            "input": text
        }
        response = self._request("/embeddings", payload)
        return self._parse_embedding_response(response)
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        result = self._call_completion(prompt, max_length, 0.3)
        return result["content"]
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        return self._call_completion_stream(prompt, max_length, 0.3)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        result = self._call_completion(prompt, 100, 0.1)
        content = result["content"]
        keywords = [k.strip() for k in content.split("，") if k.strip()]
        if not keywords:
            keywords = [k.strip() for k in content.split(",") if k.strip()]
        return keywords[:top_k]
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表：\n\n{text}"
        return self._call_completion_stream(prompt, 100, 0.1)
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        result = self._call_completion(full_prompt, 1000, 0.7)
        return {"answer": result["content"].strip(), "model": self.model_id, "usage": result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})}
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        return self._call_completion_stream(full_prompt, 1000, 0.7)
    
    def analyze_question(self, question: str) -> str:
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion(prompt, 200, 0.5)
    
    def analyze_question_detailed(self, question: str) -> dict:
        prompt = f"""请分析以下用户问题，并返回JSON格式的分析结果：

用户问题：{question}

分析规则：
1. 如果问题包含多个子问题，只要有一个子问题需要知识库回答，needs_knowledge_base就为true
2. 关于概念定义、专业术语解释、事实性知识查询的问题通常需要知识库
3. 关于系统功能、使用方法、自我介绍的问题属于系统问题
4. 日常问候、闲聊类问题不需要知识库

分析维度：
1. question_type: 问题类型，如"知识性"、"查询性"、"建议性"、"系统问题"、"闲聊"等
2. core_requirement: 核心需求，用一句话概括
3. needs_knowledge_base: 是否需要基于知识库回答，true或false
4. is_system_question: 是否是关于系统本身的问题，true或false
5. suggested_strategy: 建议的回答策略，可选值："knowledge_base"、"system_info"、"direct_answer"、"hybrid"

请仅返回JSON格式，不要包含其他内容。"""
        
        result = self._call_completion(prompt, 300, 0.3)
        try:
            analysis_data = json.loads(result["content"].strip())
            analysis_data["_usage"] = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return analysis_data
        except json.JSONDecodeError:
            default_result = self._default_analysis(question)
            default_result["_usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return default_result
    
    def analyze_question_stream(self, question: str):
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        return self._call_completion_stream(prompt, 200, 0.5)
    
    def _call_completion(self, prompt: str, max_tokens: int, temperature: float) -> dict:
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = self._request("/chat/completions", payload)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage_info = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        return {
            "content": content,
            "usage": usage_info
        }
    
    def _call_completion_stream(self, prompt: str, max_tokens: int, temperature: float):
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                first_chunk = True
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            if line == "[DONE]":
                                yield "", False, True, usage_info
                                break
                            try:
                                data = json.loads(line)
                                if "usage" in data and data["usage"]:
                                    usage_info = data["usage"]
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content, first_chunk, False, None
                                    first_chunk = False
                            except json.JSONDecodeError:
                                pass
        except requests.exceptions.RequestException as e:
            print(f"Custom stream error: {e}")
            raise HTTPException(status_code=500, detail="流式API调用失败，请稍后重试")
    
    def _default_analysis(self, question: str) -> dict:
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        if not is_system_question:
            for keyword in chat_keywords:
                if keyword in lower_question:
                    needs_knowledge_base = False
                    question_type = "闲聊"
                    suggested_strategy = "direct_answer"
                    break
        
        return {
            "question_type": question_type,
            "core_requirement": question,
            "needs_knowledge_base": needs_knowledge_base,
            "is_system_question": is_system_question,
            "suggested_strategy": suggested_strategy
        }
