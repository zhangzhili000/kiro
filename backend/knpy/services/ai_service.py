import os
import json
import dashscope
from typing import List, Dict, Optional, Any
from fastapi import HTTPException
from knpy.core.config import settings


class DashScopeClient:
    """DashScope API客户端"""
    
    def __init__(self):
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        dashscope.base_http_api_url = settings.DASHSCOPE_API_URL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.completion_model = settings.COMPLETION_MODEL
        self.timeout = 300  # 5分钟超时
        self.prompt_templates = {}  # 缓存提示词模板
    
    def set_prompt_templates(self, templates: Dict[str, str]):
        """设置提示词模板"""
        self.prompt_templates = templates
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本向量"""
        try:
            # 使用MultiModalEmbedding API
            input_data = [{'text': text}]
            response = dashscope.MultiModalEmbedding.call(
                model=self.embedding_model,
                input=input_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.output['embeddings'][0]['embedding']
            else:
                raise HTTPException(status_code=500, detail=f"Embedding API error: {response.message}")
        
        except Exception as e:
            print(f"Embedding API error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Embedding API调用失败，请稍后重试")
    
    def get_summary(self, text: str, max_length: int = 300) -> str:
        """获取文本摘要"""
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=max_length,
                temperature=0.3,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content[0]["text"]
                return content.strip()
            else:
                raise HTTPException(status_code=500, detail=f"Summary API error: {response.message}")
        
        except Exception as e:
            print(f"Summary API error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"摘要生成失败，请稍后重试")
    
    def get_summary_stream(self, text: str, max_length: int = 300):
        """流式获取文本摘要"""
        prompt = f"请对以下文本进行摘要，保持简洁，最多{max_length}字：\n\n{text}\n\n摘要："
        
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        
        response = dashscope.MultiModalConversation.call(
            model=self.completion_model,
            messages=messages,
            max_tokens=max_length,
            temperature=0.3,
            stream=True
        )
        
        for chunk in response:
            if chunk.status_code == 200:
                if hasattr(chunk, 'output') and chunk.output:
                    if hasattr(chunk.output, 'choices') and chunk.output.choices:
                        choice = chunk.output.choices[0]
                        if hasattr(choice, 'message') and choice.message:
                            content = choice.message.content
                            if isinstance(content, list) and len(content) > 0:
                                if isinstance(content[0], dict) and 'text' in content[0]:
                                    yield content[0]['text']
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表，不要包含其他内容：\n\n{text}"
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=100,
                temperature=0.1,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                if hasattr(response, 'output') and response.output:
                    if hasattr(response.output, 'choices') and response.output.choices:
                        choice = response.output.choices[0]
                        if hasattr(choice, 'message') and choice.message:
                            content = choice.message.content
                            if isinstance(content, list) and len(content) > 0:
                                if isinstance(content[0], dict) and 'text' in content[0]:
                                    keywords_text = content[0]['text']
                                    if keywords_text:
                                        keywords = [k.strip() for k in keywords_text.split("，") if k.strip()]
                                        if not keywords:
                                            keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
                                        return keywords[:top_k]
                raise HTTPException(status_code=500, detail="无法解析关键词响应")
            else:
                raise HTTPException(status_code=500, detail=f"Keywords API error: {response.message}")
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"Keywords API error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"关键词提取失败，请稍后重试")
    
    def extract_keywords_stream(self, text: str, top_k: int = 10):
        """流式提取关键词"""
        prompt = f"请从以下文本中提取最多{top_k}个关键词，仅返回用中文逗号分隔的关键词列表，不要包含其他内容：\n\n{text}"
        
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        
        response = dashscope.MultiModalConversation.call(
            model=self.completion_model,
            messages=messages,
            max_tokens=100,
            temperature=0.1,
            stream=True
        )
        
        for chunk in response:
            if chunk.status_code == 200:
                if hasattr(chunk, 'output') and chunk.output:
                    if hasattr(chunk.output, 'choices') and chunk.output.choices:
                        choice = chunk.output.choices[0]
                        if hasattr(choice, 'message') and choice.message:
                            content = choice.message.content
                            if isinstance(content, list) and len(content) > 0:
                                if isinstance(content[0], dict) and 'text' in content[0]:
                                    yield content[0]['text']
    
    def chat_completion(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> Dict[str, Any]:
        """AI对话完成"""
        # 构建完整的提示词
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": full_prompt}]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                answer = response.output.choices[0].message.content[0]["text"]
                return {
                    "answer": answer.strip(),
                    "model": self.completion_model
                }
            else:
                raise HTTPException(status_code=500, detail=f"Completion API error: {response.message}")
        
        except Exception as e:
            print(f"Chat completion error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI回答生成失败，请稍后重试")
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid") -> str:
        """构建完整的提示词，根据回答策略选择相应的提示词模板"""
        # 获取角色定义模板
        role_template = self.prompt_templates.get("role", "")
        
        # 根据回答策略选择规则模板
        strategy_template = ""
        if answer_strategy == "knowledge_base":
            strategy_template = self.prompt_templates.get("knowledge_base_rule", "")
        elif answer_strategy == "rule_based":
            strategy_template = self.prompt_templates.get("rule_based_rule", "")
        else:
            # hybrid模式，合并两种模板
            kb_rule = self.prompt_templates.get("knowledge_base_rule", "")
            rule_rule = self.prompt_templates.get("rule_based_rule", "")
            strategy_template = f"{kb_rule}\n\n{rule_rule}"
        
        # 获取格式要求模板
        format_template = self.prompt_templates.get("format", "")
        
        # 构建完整提示词
        parts = []
        
        # 角色定义
        if role_template:
            parts.append(f"角色定义：\n{role_template}")
        
        # 规则配置
        if strategy_template:
            parts.append(f"回答规则：\n{strategy_template}")
        
        # 格式要求
        if format_template:
            parts.append(f"格式要求：\n{format_template}")
        
        # 参考文档
        if context:
            parts.append(f"参考文档：\n{context}")
        
        # 用户问题
        parts.append(f"问题：{prompt}")
        
        # 最终指令
        parts.append("请根据上述信息回答问题。")
        
        return "\n\n".join(parts)

    def analyze_question(self, question: str) -> str:
        """分析用户问题"""
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 是否需要基于知识库回答（是/否）
4. 是否是关于系统本身的问题（是/否）
5. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=200,
                temperature=0.5,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                analysis = response.output.choices[0].message.content[0]["text"]
                return analysis.strip()
            else:
                raise HTTPException(status_code=500, detail=f"Analysis API error: {response.message}")
        
        except Exception as e:
            print(f"Question analysis error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"问题分析失败，请稍后重试")
    
    def analyze_question_detailed(self, question: str) -> dict:
        """详细分析用户问题，返回结构化结果"""
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
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            response = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=300,
                temperature=0.3,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content[0]["text"]
                try:
                    # 尝试解析JSON
                    result = json.loads(content.strip())
                    return result
                except json.JSONDecodeError:
                    # 如果解析失败，返回默认分析结果
                    return self._default_analysis(question)
            else:
                raise HTTPException(status_code=500, detail=f"Analysis API error: {response.message}")
        
        except HTTPException:
            raise
        except Exception as e:
            print(f"Question analysis error details: {str(e)}")
            # 返回默认分析结果
            return self._default_analysis(question)
    
    def _default_analysis(self, question: str) -> dict:
        """默认分析逻辑：基于关键词判断"""
        # 系统问题关键词
        system_keywords = ["你是谁", "什么", "功能", "使用", "帮助", "怎么", "如何", "教程", "说明", "介绍", "能做", "支持"]
        
        # 闲聊关键词
        chat_keywords = ["你好", "嗨", "hello", "hi", "在吗", "聊天", "聊"]
        
        needs_knowledge_base = True
        is_system_question = False
        question_type = "知识性"
        suggested_strategy = "knowledge_base"
        
        # 判断是否是系统问题
        lower_question = question.lower()
        for keyword in system_keywords:
            if keyword in lower_question:
                is_system_question = True
                needs_knowledge_base = False
                question_type = "系统问题"
                suggested_strategy = "system_info"
                break
        
        # 如果不是系统问题，判断是否是闲聊
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
    
    def analyze_question_stream(self, question: str):
        """流式分析用户问题"""
        prompt = f"""请分析以下用户问题，包括：
1. 问题类型（如：知识性、查询性、建议性等）
2. 核心需求
3. 可能需要的信息类型
4. 回答策略建议

请用简洁的语言分析，不超过200字。

用户问题：{question}"""
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            responses = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=200,
                temperature=0.5,
                timeout=self.timeout,
                stream=True
            )
            
            for response in responses:
                if response.status_code == 200:
                    if hasattr(response, 'output') and response.output:
                        if hasattr(response.output, 'choices') and response.output.choices:
                            choice = response.output.choices[0]
                            if hasattr(choice, 'message') and choice.message:
                                content = choice.message.content
                                if isinstance(content, list) and len(content) > 0:
                                    if isinstance(content[0], dict) and 'text' in content[0]:
                                        text = content[0]['text']
                                        yield text, False
            yield "", True
        
        except Exception as e:
            print(f"Stream question analysis error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"问题分析失败，请稍后重试")
    
    def chat_completion_stream(self, prompt: str, context: Optional[str] = None, answer_strategy: str = "hybrid"):
        """流式AI对话完成"""
        # 构建完整的提示词
        full_prompt = self._build_prompt(prompt, context, answer_strategy)
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": full_prompt}]
                }
            ]
            
            responses = dashscope.MultiModalConversation.call(
                model=self.completion_model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                timeout=self.timeout,
                stream=True
            )
            
            is_first = True
            for response in responses:
                if response.status_code == 200:
                    if hasattr(response, 'output') and response.output:
                        if hasattr(response.output, 'choices') and response.output.choices:
                            choice = response.output.choices[0]
                            if hasattr(choice, 'message') and choice.message:
                                content = choice.message.content
                                if isinstance(content, list) and len(content) > 0:
                                    if isinstance(content[0], dict) and 'text' in content[0]:
                                        text = content[0]['text']
                                        yield text, is_first, False
                                        is_first = False
            # 发送完成信号
            yield "", False, True
        
        except Exception as e:
            print(f"Stream chat completion error details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI回答生成失败，请稍后重试")


class FAISSService:
    """FAISS向量索引服务"""
    
    def __init__(self):
        import faiss
        self.index = None
        self.documents = []
        self.index_path = settings.FAISS_INDEX_PATH
        self._ensure_path()
    
    def _ensure_path(self):
        """确保索引目录存在"""
        os.makedirs(self.index_path, exist_ok=True)
    
    def create_index(self, dimension: int = 1024):
        """创建向量索引"""
        import faiss
        self.index = faiss.IndexFlatL2(dimension)
    
    def add_vectors(self, vectors: List[List[float]], documents: List[Dict]):
        """添加向量到索引"""
        import numpy as np
        
        if self.index is None:
            self.create_index(len(vectors[0]))
        
        np_vectors = np.array(vectors, dtype=np.float32)
        self.index.add(np_vectors)
        self.documents.extend(documents)
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """搜索相似向量"""
        import numpy as np
        
        if self.index is None:
            return []
        
        np_query = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(np_query, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                results.append({
                    "distance": float(distances[0][i]),
                    **self.documents[idx]
                })
        
        return results
    
    def save_index(self, filename: str = "document_index"):
        """保存索引到文件"""
        import faiss
        
        if self.index is not None:
            faiss.write_index(self.index, os.path.join(self.index_path, f"{filename}.idx"))
            
            with open(os.path.join(self.index_path, f"{filename}_docs.json"), "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False)
    
    def load_index(self, filename: str = "document_index"):
        """从文件加载索引"""
        import faiss
        
        index_file = os.path.join(self.index_path, f"{filename}.idx")
        docs_file = os.path.join(self.index_path, f"{filename}_docs.json")
        
        if os.path.exists(index_file) and os.path.exists(docs_file):
            self.index = faiss.read_index(index_file)
            
            with open(docs_file, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            
            # 自动转换旧格式的文档数据
            need_save = False
            for doc in self.documents:
                if "chunk_content" not in doc and "content" in doc:
                    doc["chunk_content"] = doc["content"]
                    doc["document_title"] = doc.get("title", "")
                    doc["chunk_index"] = 0
                    need_save = True
                # 确保 document_id 是字符串
                if "document_id" in doc and not isinstance(doc["document_id"], str):
                    doc["document_id"] = str(doc["document_id"])
                    need_save = True
            
            if need_save:
                self.save_index(filename)
                print("Converted old index format to new format and saved")


faiss_service = FAISSService()
