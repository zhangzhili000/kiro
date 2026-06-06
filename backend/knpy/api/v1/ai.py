from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import uuid
from uuid import UUID
import os
import asyncio
import json
import time

from knpy.core.database import get_db
from knpy.core.config import settings
from knpy.services.ai_service import faiss_service
from knpy.services.model_service import DynamicAIClient
from knpy.services.document_parser_service import document_parser
from knpy.models.document import Document
from knpy.models.ai_models import DocumentVector, AIConversation
from knpy.schemas.ai_schemas import (
    DocumentConvertRequest,
    DocumentConvertResponse,
    DocumentProcessRequest,
    DocumentProcessResponse,
    DocumentSummaryResponse,
    DocumentKeywordsResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationHistoryResponse,
    UpdateConversationTitleRequest,
    UpdateConversationTitleResponse,
    StreamEventType,
    StepEventData,
    SearchResultEventData,
    ContentEventData,
    QuestionAnalysisEventData,
    RoleDefinition,
    AIRules,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    AIConfigResponse
)
from knpy.models.ai_models import AIConfig, PromptTemplate
from knpy.api.v1.users import get_current_user
from knpy.models.user import User
from knpy.core.timezone_utils import get_beijing_time

router = APIRouter(prefix="/ai", tags=["AI"])

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 全局提示词模板缓存
prompt_templates_cache = {}

# 正在运行的流式对话状态管理
active_conversations = {}  # {conversation_uuid: {"stop": False, "task": None}}

# 获取AI客户端依赖
def get_ai_client(db: Session = Depends(get_db)):
    client = DynamicAIClient(db)
    client.set_prompt_templates(prompt_templates_cache)
    return client


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传文档并自动进行格式转换"""
    try:
        # 验证文件类型
        allowed_extensions = ['.pdf', '.doc', '.docx', '.md', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅支持: {', '.join(allowed_extensions)}")
        
        # 保存上传的文件
        temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 解析文件
        result = document_parser.parse_file(temp_file_path, file_extension[1:])
        
        # 获取HTML内容（优先使用解析结果中已有的html_content）
        if "html_content" in result and result["html_content"]:
            html_content = result["html_content"]
        else:
            # 转换为HTML（包含表格和图片）
            tables = result.get("tables", [])
            images = result.get("images", [])
            html_content = document_parser.convert_to_html(result["content"], result["type"], tables, images)
        
        # 删除临时文件
        os.remove(temp_file_path)
        
        return {
            "success": True,
            "original_filename": file.filename,
            "content": result["content"],
            "html_content": html_content,
            "metadata": result.get("metadata"),
            "file_type": result["type"],
            "tables": result.get("tables", []),
            "images": result.get("images", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/convert", response_model=DocumentConvertResponse)
async def convert_document(request: DocumentConvertRequest):
    """文档格式转换"""
    try:
        result = document_parser.parse_file(request.file_path, request.file_type)
        html_content = document_parser.convert_to_html(result["content"], result["type"])
        
        return DocumentConvertResponse(
            success=True,
            content=result["content"],
            html_content=html_content,
            metadata=result.get("metadata"),
            file_type=result["type"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """处理文档（摘要+关键词+向量化）"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # 分块处理文档内容
        chunks = document_parser.split_content(document.content)
        
        # 获取文档摘要
        summary = ai_client.get_summary(document.content)
        
        # 提取关键词
        keywords = ai_client.extract_keywords(document.content)
        
        # 向量化每个块
        vectors = []
        documents_meta = []
        
        for idx, chunk in enumerate(chunks):
            embedding = ai_client.get_embedding(chunk)
            vectors.append(embedding)
            
            chunk_summary = ai_client.get_summary(chunk, max_length=100)
            chunk_keywords = ai_client.extract_keywords(chunk, top_k=5)
            
            # 保存到数据库
            vector_record = DocumentVector(
                document_id=document_id,
                chunk_index=idx,
                chunk_content=chunk,
                chunk_summary=chunk_summary,
                keywords=chunk_keywords,
                vector_data=bytes(embedding)
            )
            db.add(vector_record)
            
            documents_meta.append({
                "document_id": str(document_id),
                "document_title": document.title,
                "chunk_index": idx,
                "chunk_content": chunk
            })
        
        db.commit()
        
        # 添加到FAISS索引
        if vectors:
            faiss_service.add_vectors(vectors, documents_meta)
            faiss_service.save_index()
        
        return DocumentProcessResponse(
            success=True,
            document_id=document_id,
            chunks_count=len(chunks),
            summary=summary,
            keywords=keywords
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/summary")
async def generate_summary(
    request: dict,
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """根据内容生成摘要"""
    content = request.get('content', '')
    if not content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    try:
        summary = ai_client.get_summary(content)
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/summary/stream")
async def generate_summary_stream(
    request: dict,
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """流式生成摘要（逐字显示）"""
    content = request.get('content', '')
    if not content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    async def stream_summary():
        try:
            buffer = ""
            for chunk in ai_client.get_summary_stream(content):
                buffer += chunk
                # 逐个字符发送，实现真正的流式效果
                for char in buffer:
                    yield f"data: {char}\n\n"
                    await asyncio.sleep(0.02)
                buffer = ""
            # 发送剩余内容
            for char in buffer:
                yield f"data: {char}\n\n"
                await asyncio.sleep(0.02)
            yield "data: [END]\n\n"
        except Exception as e:
            yield f"data: [ERROR]{str(e)}[/ERROR]\n\n"
    
    headers = {
        "Cache-Control": "no-cache",
        "Transfer-Encoding": "chunked",
        "X-Accel-Buffering": "no",
        "Content-Type": "text/event-stream"
    }
    
    return StreamingResponse(stream_summary(), headers=headers)


@router.post("/documents/keywords")
async def extract_keywords(
    request: dict,
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """根据内容提取关键词"""
    content = request.get('content', '')
    if not content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    try:
        keywords = ai_client.extract_keywords(content)
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/keywords/stream")
async def extract_keywords_stream(
    request: dict,
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """流式提取关键词（逐字显示）"""
    content = request.get('content', '')
    if not content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    async def stream_keywords():
        try:
            buffer = ""
            for chunk in ai_client.extract_keywords_stream(content):
                buffer += chunk
                # 逐个字符发送，实现真正的流式效果
                for char in buffer:
                    yield f"data: {char}\n\n"
                    await asyncio.sleep(0.02)
                buffer = ""
            # 发送剩余内容
            for char in buffer:
                yield f"data: {char}\n\n"
                await asyncio.sleep(0.02)
            yield "data: [END]\n\n"
        except Exception as e:
            yield f"data: [ERROR]{str(e)}[/ERROR]\n\n"
    
    headers = {
        "Cache-Control": "no-cache",
        "Transfer-Encoding": "chunked",
        "X-Accel-Buffering": "no",
        "Content-Type": "text/event-stream"
    }
    
    return StreamingResponse(stream_keywords(), headers=headers)


@router.get("/documents/{document_id}/summary", response_model=DocumentSummaryResponse)
async def get_document_summary(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """获取文档摘要"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        summary = ai_client.get_summary(document.content)
        return DocumentSummaryResponse(document_id=document_id, summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/keywords", response_model=DocumentKeywordsResponse)
async def get_document_keywords(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """获取文档关键词"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        keywords = ai_client.extract_keywords(document.content)
        return DocumentKeywordsResponse(document_id=document_id, keywords=keywords)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectors/search", response_model=VectorSearchResponse)
async def search_vectors(
    request: VectorSearchRequest,
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """向量相似性检索"""
    try:
        # 获取查询向量
        query_vector = ai_client.get_embedding(request.query)
        
        # 搜索FAISS索引
        results = faiss_service.search(query_vector, request.top_k)
        
        # 转换为响应格式
        search_results = []
        for result in results:
            search_results.append(VectorSearchResult(
                document_id=result["document_id"],
                document_title=result.get("document_title"),
                chunk_content=result["chunk_content"],
                distance=result["distance"],
                chunk_index=result["chunk_index"]
            ))
        
        return VectorSearchResponse(results=search_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectors/index")
async def build_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """构建/更新向量索引"""
    try:
        # 加载所有文档向量
        vectors = db.query(DocumentVector).all()
        
        if not vectors:
            raise HTTPException(status_code=400, detail="No document vectors found")
        
        # 重建FAISS索引
        faiss_service.create_index()
        
        all_vectors = []
        all_docs = []
        
        for v in vectors:
            vector_data = list(v.vector_data)
            all_vectors.append(vector_data)
            
            document = db.query(Document).filter(Document.id == v.document_id).first()
            all_docs.append({
                "document_id": str(v.document_id),
                "document_title": document.title if document else None,
                "chunk_index": v.chunk_index,
                "chunk_content": v.chunk_content
            })
        
        faiss_service.add_vectors(all_vectors, all_docs)
        faiss_service.save_index()
        
        return {"success": True, "vectors_count": len(vectors)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vectors/{document_id}")
async def delete_document_vectors(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文档向量"""
    try:
        # 删除数据库中的向量记录
        db.query(DocumentVector).filter(DocumentVector.document_id == document_id).delete()
        db.commit()
        
        # 重建索引
        build_index(db, current_user)
        
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """AI对话"""
    
    try:
        context = None
        referenced_docs = []
        use_knowledge_base = True
        
        # 记录开始时间
        question_time = get_beijing_time()
        start_time = time.time()
        
        # 获取AI配置
        ai_config = db.query(AIConfig).first()
        answer_strategy = "hybrid"
        temperature = 0.7
        
        if ai_config:
            rules = ai_config.rules
            answer_strategy = rules.get("answerStrategy", "hybrid")
            temperature = rules.get("temperature", 0.7)
        
        # 步骤1: 分析问题 - 判断是否需要基于知识库回答
        analysis_result = ai_client.analyze_question_detailed(request.question)
        needs_knowledge_base = analysis_result.get("needs_knowledge_base", True)
        is_system_question = analysis_result.get("is_system_question", False)
        suggested_strategy = analysis_result.get("suggested_strategy", answer_strategy)
        
        # 根据分析结果决定是否使用知识库
        if not needs_knowledge_base:
            use_knowledge_base = False
            
            # 步骤2: 如果不需要知识库，检查是否是系统问题
            if is_system_question:
                # 步骤3: 如果是系统问题，使用AI配置中的信息作为上下文
                if ai_config:
                    role_def = ai_config.role_definition
                    system_info = f"系统信息：\n角色名称：{role_def.get('name', '')}\n角色描述：{role_def.get('description', '')}\n行为准则：{role_def.get('guidelines', '')}"
                    context = system_info
                answer_strategy = "system_info"
            else:
                # 非系统问题且不需要知识库，拒绝回答
                raise HTTPException(status_code=400, detail="抱歉，我只能回答与知识库相关的问题或关于系统本身的问题。")
        
        # 如果需要基于知识库回答
        embedding_tokens = 0
        if use_knowledge_base and request.use_context:
            # 获取相关文档（最多15份）
            embedding_result = ai_client.get_embedding(request.question)
            query_vector = embedding_result.get("embedding", [])
            embedding_usage = embedding_result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            embedding_tokens = embedding_usage.get("total_tokens", 0)
            results = faiss_service.search(query_vector, top_k=15)
            
            # 过滤相似度≥0.6的文档（相似度 = 1 - distance）
            relevant_results = []
            if results:
                for r in results:
                    distance = r.get("distance", 1.0)
                    similarity = 1 - distance
                    if similarity >= 0.6:
                        relevant_results.append(r)
            
            if relevant_results:
                context = "\n\n".join([f"文档{idx+1}：\n{r.get('chunk_content', r.get('content', ''))}" for idx, r in enumerate(relevant_results)])
                referenced_docs = [{
                    "document_id": r["document_id"],
                    "document_title": r.get("document_title", r.get("title", "")),
                    "chunk_index": r.get("chunk_index", 0),
                    "distance": r["distance"]
                } for r in relevant_results]
        
        # 生成回答（使用动态提示词配置）
        response = ai_client.chat_completion(request.question, context, answer_strategy)
        
        # 计算结束时间和耗时
        answer_time = get_beijing_time()
        duration = int((time.time() - start_time) * 1000)
        
        # 使用真实的token数量
        chat_usage = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        tokens = embedding_tokens + chat_usage.get("total_tokens", 0)
        
        # 获取模型名称
        model_name = response.get("model", "unknown")
        
        # 保存对话记录
        conversation = AIConversation(
            user_id=current_user.id,
            question=request.question,
            answer=response["answer"],
            referenced_docs=referenced_docs if referenced_docs else None,
            model=model_name,
            tokens=tokens,
            question_time=question_time,
            answer_time=answer_time,
            duration=duration
        )
        db.add(conversation)
        db.commit()
        
        return ChatResponse(
            answer=response["answer"],
            referenced_docs=referenced_docs,
            model=response["model"],
            created_at=conversation.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history", response_model=ConversationListResponse)
async def get_chat_history(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话历史"""
    print(f"Getting chat history for user: {current_user.id}, limit: {limit}")
    
    # 添加分页限制，最多返回100条记录
    conversations = db.query(AIConversation)\
        .filter(AIConversation.user_id == current_user.id)\
        .order_by(AIConversation.created_at.desc())\
        .limit(min(limit, 100))\
        .all()
    
    print(f"Found {len(conversations)} conversations")
    
    history = []
    for conv in conversations:
        # print(f"Conversation: id={conv.id}, question={conv.question[:30]}...")
        # print(f"Processing steps: {conv.processing_steps}")
        history.append(ConversationHistoryResponse(
            id=conv.id,
            conversation_uuid=conv.conversation_uuid,
            title=conv.title,
            question=conv.question,
            answer=conv.answer,
            model=conv.model,
            tokens=conv.tokens,
            question_time=conv.question_time,
            answer_time=conv.answer_time,
            duration=conv.duration,
            processing_steps=conv.processing_steps,
            status=getattr(conv, 'status', 'completed'),
            created_at=conv.created_at
        ))
    
    response = ConversationListResponse(conversations=history)
    print(f"Returning response with {len(history)} conversations")
    
    return response


@router.put("/chat/conversation/title", response_model=UpdateConversationTitleResponse)
async def update_conversation_title(
    request: UpdateConversationTitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新对话标题"""
    # 查找该用户的所有具有该 conversation_uuid 的对话
    conversations = db.query(AIConversation)\
        .filter(AIConversation.conversation_uuid == request.conversation_uuid)\
        .filter(AIConversation.user_id == current_user.id)\
        .all()
    
    if not conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # 更新所有对话的标题
    for conv in conversations:
        conv.title = request.title
    
    db.commit()
    
    return UpdateConversationTitleResponse(
        success=True,
        conversation_uuid=request.conversation_uuid,
        title=request.title
    )


@router.delete("/chat/history/{conversation_id}")
async def delete_chat_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除单条对话记录"""
    conversation = db.query(AIConversation)\
        .filter(AIConversation.id == conversation_id)\
        .filter(AIConversation.user_id == current_user.id)\
        .first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    
    return {"success": True}


@router.get("/chat/conversation/{conversation_uuid}")
async def get_conversation_by_uuid(
    conversation_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定对话UUID的所有问答记录（上限50条）"""
    print(f"Getting conversation by UUID: {conversation_uuid} for user: {current_user.id}")
    
    # 将UUID对象转换为字符串
    conversation_uuid_str = str(conversation_uuid)
    
    # 获取同一会话的所有问答记录，按时间升序排列，最多50条
    conversations = db.query(AIConversation)\
        .filter(AIConversation.conversation_uuid == conversation_uuid_str)\
        .filter(AIConversation.user_id == current_user.id)\
        .order_by(AIConversation.created_at.asc())\
        .limit(50)\
        .all()
    
    if not conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = []
    for conv in conversations:
        history.append(ConversationHistoryResponse(
            id=conv.id,
            conversation_uuid=conv.conversation_uuid,
            title=conv.title,
            question=conv.question,
            answer=conv.answer,
            model=conv.model,
            tokens=conv.tokens,
            question_time=conv.question_time,
            answer_time=conv.answer_time,
            duration=conv.duration,
            processing_steps=conv.processing_steps,
            status=getattr(conv, 'status', 'completed'),
            created_at=conv.created_at
        ))
    
    response = ConversationListResponse(conversations=history)
    print(f"Returning {len(history)} messages for conversation {conversation_uuid}")
    
    return response


@router.delete("/chat/conversation/{conversation_uuid}")
async def delete_conversation_session(
    conversation_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除整个对话会话（按conversation_uuid）"""
    # 将UUID对象转换为字符串，因为数据库中存储的是String类型
    conversation_uuid_str = str(conversation_uuid)
    conversations = db.query(AIConversation)\
        .filter(AIConversation.conversation_uuid == conversation_uuid_str)\
        .filter(AIConversation.user_id == current_user.id)\
        .all()
    
    if not conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    for conv in conversations:
        db.delete(conv)
    
    db.commit()
    
    return {"success": True, "deleted_count": len(conversations)}


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_client: DynamicAIClient = Depends(get_ai_client)
):
    """流式AI对话 - 展示处理步骤和流式回答"""
    
    # 估算 token 数量（简单估算：中文每2个字符算1个token，英文每4个字符算1个token）
    def estimate_tokens(text):
        if not text:
            return 0
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return (chinese_chars // 2) + (other_chars // 4)
    
    async def stream_generator():
        try:
            # 记录开始时间
            question_time = get_beijing_time()
            start_time = time.time()
            
            # 生成 conversation_uuid（如果没有提供）
            conversation_uuid = str(request.conversation_uuid) if request.conversation_uuid else str(uuid.uuid4())
            
            # 注册当前对话为活跃状态
            active_conversations[conversation_uuid] = {"stop": False, "task": None}
            
            # 检查是否已被终止（可能在注册前就被终止）
            if active_conversations.get(conversation_uuid, {}).get("stop", False):
                yield f"data: {json.dumps({'type': StreamEventType.ERROR, 'data': {'message': '对话已被终止'}})}\n\n"
                return
            
            # 立即保存待处理状态的对话记录
            pending_conversation = AIConversation(
                user_id=current_user.id,
                question=request.question,
                answer="",
                question_time=question_time,
                conversation_uuid=conversation_uuid,
                status="pending",
                conversation_mode=request.conversation_mode if hasattr(request, 'conversation_mode') else "fast_qa"
            )
            db.add(pending_conversation)
            db.commit()
            db.refresh(pending_conversation)
            
            # 获取AI配置
            ai_config = db.query(AIConfig).first()
            answer_strategy = "hybrid"
            
            if ai_config:
                rules = ai_config.rules
                answer_strategy = rules.get("answerStrategy", "hybrid")
            
            # 存储所有步骤信息
            steps_info = []
            
            # 获取当前使用的模型配置
            chat_model_name = "unknown"
            embedding_model_name = "unknown"
            try:
                chat_config = ai_client.config_service.get_active_config("chat")
                if chat_config:
                    chat_model_name = chat_config.get("model_id", "unknown")
                embedding_config = ai_client.config_service.get_active_config("embedding")
                if embedding_config:
                    embedding_model_name = embedding_config.get("model_id", "unknown")
            except Exception:
                pass
            
            # 多轮对话相关变量
            history_summary = ""
            history_compression_tokens = 0
            conversation_mode = request.conversation_mode if hasattr(request, 'conversation_mode') else "fast_qa"
            
            # 如果是多轮对话模式且有对话UUID，获取历史对话并压缩
            if conversation_mode == "multi_round" and request.conversation_uuid:
                # 获取同一会话的历史对话（按时间排序，最多获取最近10条）
                history_conversations = db.query(AIConversation)\
                    .filter(AIConversation.conversation_uuid == request.conversation_uuid)\
                    .filter(AIConversation.user_id == current_user.id)\
                    .order_by(AIConversation.created_at.asc())\
                    .limit(10)\
                    .all()
                
                if history_conversations:
                    # 步骤 0: 历史对话压缩（仅多轮对话模式）
                    step0_start = time.time()
                    step_data = StepEventData(
                        step=0,
                        title="历史对话压缩",
                        description="正在分析历史对话...",
                        status="in_progress",
                        model=chat_model_name,
                        tokens=None
                    )
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    # 构建历史对话列表
                    history_list = []
                    for conv in history_conversations:
                        history_list.append({
                            "question": conv.question,
                            "answer": conv.answer
                        })
                    
                    # 使用LLM压缩历史对话
                    compression_result = ai_client.compress_conversation_history(history_list, max_length=300)
                    history_summary = compression_result.get("summary", "")
                    history_usage = compression_result.get("usage", {})
                    history_compression_tokens = history_usage.get("total_tokens", 0)
                    
                    step0_duration = int((time.time() - step0_start) * 1000)
                    
                    step_data.status = "completed"
                    step_data.description = f"历史对话压缩完成（模型：{chat_model_name}，消耗：{history_compression_tokens} tokens）"
                    step_data.tokens = history_compression_tokens
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    steps_info.append({
                        "step": 0,
                        "title": "历史对话压缩",
                        "description": step_data.description,
                        "duration": step0_duration,
                        "model": chat_model_name,
                        "tokens": history_compression_tokens,
                        "history_summary": history_summary
                    })
            
            # 步骤 1: 理解提问
            step1_start = time.time()
            step_data = StepEventData(
                step=1,
                title="理解提问",
                description="正在分析您的问题...",
                status="in_progress",
                model=chat_model_name,
                tokens=None
            )
            yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
            
            # 详细分析问题（按照要求的步骤）
            # 如果是多轮对话模式且有历史摘要，将其传递给问题分析
            analysis_result = ai_client.analyze_question_detailed(request.question, history_summary)
            needs_knowledge_base = analysis_result.get("needs_knowledge_base", True)
            is_system_question = analysis_result.get("is_system_question", False)
            suggested_strategy = analysis_result.get("suggested_strategy", answer_strategy)
            
            # 获取步骤1的真实token使用量
            step1_usage = analysis_result.get("_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            step1_tokens = step1_usage.get("total_tokens", 0)
            
            # 流式分析结果展示
            question_analysis_result = f"问题类型：{analysis_result.get('question_type', '')}\n核心需求：{analysis_result.get('core_requirement', '')}\n需要知识库：{'是' if needs_knowledge_base else '否'}\n系统问题：{'是' if is_system_question else '否'}\n建议策略：{suggested_strategy}"
            
            analysis_event = QuestionAnalysisEventData(
                content=question_analysis_result,
                is_complete=True
            )
            yield f"data: {json.dumps({'type': StreamEventType.QUESTION_ANALYSIS, 'data': analysis_event.model_dump()})}\n\n"
            
            step1_duration = int((time.time() - step1_start) * 1000)
            
            # 步骤 1 完成
            step_data.status = "completed"
            step_data.description = f"问题分析完成（模型：{chat_model_name}，消耗：{step1_tokens} tokens）"
            step_data.tokens = step1_tokens
            yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
            
            steps_info.append({
                "step": 1,
                "title": "理解提问",
                "description": f"问题分析完成（模型：{chat_model_name}，消耗：{step1_tokens} tokens）",
                "duration": step1_duration,
                "model": chat_model_name,
                "tokens": step1_tokens,
                "analysis": question_analysis_result,
                "needs_knowledge_base": needs_knowledge_base,
                "is_system_question": is_system_question
            })
            
            # 检查是否被终止
            if active_conversations.get(conversation_uuid, {}).get("stop", False):
                yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': {'content': '对话已被用户终止。', 'is_first': True, 'is_last': True}})}\n\n"
                pending_conversation.answer = "对话已被用户终止。"
                pending_conversation.status = "completed"
                db.commit()
                yield f"data: {json.dumps({
                    'type': StreamEventType.DONE, 
                    'data': {
                        'conversation_id': pending_conversation.id,
                        'conversation_uuid': conversation_uuid,
                        'model': chat_model_name,
                        'tokens': step1_tokens,
                        'question_time': question_time.isoformat(),
                        'answer_time': get_beijing_time().isoformat(),
                        'duration': int((time.time() - start_time) * 1000),
                        'processing_steps': steps_info
                    }
                })}\n\n"
                return
            
            context = None
            referenced_docs = []
            search_results = []
            
            has_relevant_content = False
            use_knowledge_base = needs_knowledge_base and request.use_context
            
            # 如果不需要知识库，但需要检查是否是系统问题
            if not needs_knowledge_base:
                if is_system_question:
                    # 使用AI配置中的信息作为上下文
                    if ai_config:
                        role_def = ai_config.role_definition
                        system_info = f"系统信息：\n角色名称：{role_def.get('name', '')}\n角色描述：{role_def.get('description', '')}\n行为准则：{role_def.get('guidelines', '')}"
                        context = system_info
                    answer_strategy = "system_info"
                else:
                    # 非系统问题且不需要知识库，拒绝回答
                    content_data = ContentEventData(
                        content="抱歉，我只能回答与知识库相关的问题或关于系统本身的问题。",
                        is_first=True,
                        is_last=True
                    )
                    yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
                    
                    # 发送完成信号
                    answer_time = get_beijing_time()
                    duration = int((time.time() - start_time) * 1000)
                    
                    yield f"data: {json.dumps({
                        'type': StreamEventType.DONE, 
                        'data': {
                            'conversation_id': None,
                            'conversation_uuid': None,
                            'model': chat_model_name,
                            'tokens': step1_tokens,
                            'question_time': question_time.isoformat(),
                            'answer_time': answer_time.isoformat(),
                            'duration': duration,
                            'processing_steps': steps_info
                        }
                    })}\n\n"
                    return
            
            if use_knowledge_base:
                # 步骤 2: 检索相关内容
                step2_start = time.time()
                step_data = StepEventData(
                    step=2,
                    title="检索相关内容",
                    description="正在从知识库中查找相关文档...",
                    status="in_progress",
                    model=embedding_model_name,
                    tokens=None
                )
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                
                # 构建检索查询：如果是多轮对话，结合历史对话摘要和当前问题
                search_query = request.question
                if history_summary:
                    # 将历史对话摘要与当前问题融合，进行Query改写
                    search_query = f"基于以下对话历史，回答当前问题：\n历史对话：{history_summary}\n当前问题：{request.question}"
                
                # 获取相关文档（最多15份）
                embedding_result = ai_client.get_embedding(search_query)
                query_vector = embedding_result.get("embedding", [])
                step2_usage = embedding_result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                step2_tokens = step2_usage.get("total_tokens", 0)
                results = faiss_service.search(query_vector, top_k=15)
                
                # 过滤相似度≥0.6的文档（相似度 = 1 - distance）
                relevant_results = []
                if results:
                    for r in results:
                        distance = r.get("distance", 1.0)
                        similarity = 1 - distance
                        if similarity >= 0.6:
                            relevant_results.append(r)
                
                if relevant_results:
                    has_relevant_content = True
                    
                    # 兼容旧索引结构和新索引结构
                    def get_chunk_content(r):
                        return r.get("chunk_content", r.get("content", ""))
                    
                    def get_document_title(r):
                        return r.get("document_title", r.get("title", ""))
                    
                    def get_chunk_index(r):
                        return r.get("chunk_index", 0)
                    
                    context = "\n\n".join([f"文档{idx+1}：\n{get_chunk_content(r)}" for idx, r in enumerate(relevant_results)])
                    referenced_docs = [{
                        "document_id": r["document_id"],
                        "document_title": get_document_title(r),
                        "chunk_index": get_chunk_index(r),
                        "distance": r["distance"]
                    } for r in relevant_results]
                    
                    search_results = [{
                        "document_id": str(r["document_id"]),
                        "document_title": get_document_title(r),
                        "chunk_content": get_chunk_content(r),
                        "distance": r["distance"],
                        "chunk_index": get_chunk_index(r)
                    } for r in relevant_results]
                    
                    # 发送搜索结果
                    search_result_data = SearchResultEventData(results=[
                        {
                            "document_id": str(r["document_id"]),
                            "document_title": get_document_title(r),
                            "chunk_content": get_chunk_content(r)[:100] + "..." if len(get_chunk_content(r)) > 100 else get_chunk_content(r),
                            "distance": r["distance"],
                            "chunk_index": get_chunk_index(r)
                        } for r in relevant_results
                    ])
                    yield f"data: {json.dumps({'type': StreamEventType.SEARCH_RESULT, 'data': search_result_data.model_dump()})}\n\n"
                
                step2_duration = int((time.time() - step2_start) * 1000)
                
                # 步骤 2 完成
                step_data.status = "completed"
                if has_relevant_content:
                    step_data.description = f"找到 {len(relevant_results)} 条相关内容（模型：{embedding_model_name}，消耗：{step2_tokens} tokens）"
                else:
                    step_data.description = f"未找到足够相关的内容（模型：{embedding_model_name}，消耗：{step2_tokens} tokens）"
                step_data.tokens = step2_tokens
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                
                steps_info.append({
                    "step": 2,
                    "title": "检索相关内容",
                    "description": step_data.description,
                    "duration": step2_duration,
                    "model": embedding_model_name,
                    "tokens": step2_tokens,
                    "search_results": search_results if has_relevant_content else []
                })
            else:
                # 跳过步骤 2（不需要知识库或已禁用）
                skip_reason = "已跳过知识库检索"
                if not needs_knowledge_base:
                    skip_reason = "分析结果：不需要基于知识库回答"
                    if is_system_question:
                        skip_reason += "，将使用系统配置信息回答"
                
                step_data = StepEventData(
                    step=2,
                    title="检索相关内容",
                    description=skip_reason,
                    status="completed"
                )
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                
                steps_info.append({
                    "step": 2,
                    "title": "检索相关内容",
                    "description": skip_reason,
                    "duration": 0
                })
            
            # 检查是否被终止
            if active_conversations.get(conversation_uuid, {}).get("stop", False):
                yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': {'content': '对话已被用户终止。', 'is_first': True, 'is_last': True}})}\n\n"
                pending_conversation.answer = "对话已被用户终止。"
                pending_conversation.status = "completed"
                db.commit()
                yield f"data: {json.dumps({
                    'type': StreamEventType.DONE, 
                    'data': {
                        'conversation_id': pending_conversation.id,
                        'conversation_uuid': conversation_uuid,
                        'model': chat_model_name,
                        'tokens': step1_tokens + (step2_tokens if 'step2_tokens' in locals() else 0),
                        'question_time': question_time.isoformat(),
                        'answer_time': get_beijing_time().isoformat(),
                        'duration': int((time.time() - start_time) * 1000),
                        'processing_steps': steps_info
                    }
                })}\n\n"
                return
            
            if has_relevant_content or is_system_question:
                # 步骤 4: 组合上下文
                step4_start = time.time()
                step_data = StepEventData(
                    step=4,
                    title="组合上下文",
                    description="正在准备AI回答的上下文...",
                    status="in_progress",
                    model=None,
                    tokens=None
                )
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                await asyncio.sleep(0.3)
                
                # 如果是多轮对话模式且有历史摘要，将其添加到上下文前面
                if history_summary:
                    context = f"历史对话摘要：\n{history_summary}\n\n{context}" if context else f"历史对话摘要：\n{history_summary}"
                
                step4_duration = int((time.time() - step4_start) * 1000)
                
                step_data.status = "completed"
                step_data.description = "上下文准备完成"
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                
                steps_info.append({
                    "step": 4,
                    "title": "组合上下文",
                    "description": "上下文准备完成",
                    "duration": step4_duration,
                    "model": None,
                    "tokens": None
                })
                
                # 检查是否被终止
                if active_conversations.get(conversation_uuid, {}).get("stop", False):
                    yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': {'content': '对话已被用户终止。', 'is_first': True, 'is_last': True}})}\n\n"
                    pending_conversation.answer = "对话已被用户终止。"
                    pending_conversation.status = "completed"
                    db.commit()
                    yield f"data: {json.dumps({
                        'type': StreamEventType.DONE, 
                        'data': {
                            'conversation_id': pending_conversation.id,
                            'conversation_uuid': conversation_uuid,
                            'model': chat_model_name,
                            'tokens': step1_tokens + (step2_tokens if 'step2_tokens' in locals() else 0),
                            'question_time': question_time.isoformat(),
                            'answer_time': get_beijing_time().isoformat(),
                            'duration': int((time.time() - start_time) * 1000),
                            'processing_steps': steps_info
                        }
                    })}\n\n"
                    return
                
                # 步骤 5: AI 回答
                step5_start = time.time()
                step_data = StepEventData(
                    step=5,
                    title="AI 回答",
                    description="正在生成回答...",
                    status="in_progress",
                    model=chat_model_name,
                    tokens=None
                )
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                
                # 流式生成 AI 回答（使用动态提示词配置）
                full_answer = ""
                is_first_content = True
                step5_usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                for text, is_first, is_last, usage_info in ai_client.chat_completion_stream(request.question, context, answer_strategy):
                    # 检查是否被终止
                    if active_conversations.get(conversation_uuid, {}).get("stop", False):
                        if full_answer:
                            content_data = ContentEventData(
                                content="\n\n对话已被用户终止。",
                                is_first=False,
                                is_last=True
                            )
                            yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
                        else:
                            content_data = ContentEventData(
                                content="对话已被用户终止。",
                                is_first=True,
                                is_last=True
                            )
                            yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
                        full_answer += "\n\n对话已被用户终止。"
                        break
                    
                    if text:
                        full_answer += text
                        content_data = ContentEventData(
                            content=text,
                            is_first=is_first_content,
                            is_last=is_last and not active_conversations.get(conversation_uuid, {}).get("stop", False)
                        )
                        yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
                        is_first_content = False
                    # 收集最后一个chunk中的usage信息
                    if is_last and usage_info:
                        step5_usage_info = usage_info
                
                step5_duration = int((time.time() - step5_start) * 1000)
                
                # 使用真实的token使用量
                step5_tokens = step5_usage_info.get("total_tokens", 0)
                
                # 步骤 5 完成
                step_data.status = "completed"
                step_data.description = f"回答生成完成（模型：{chat_model_name}，消耗：{step5_tokens} tokens）"
                step_data.tokens = step5_tokens
                yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                
                steps_info.append({
                    "step": 5,
                    "title": "AI 回答",
                    "description": f"回答生成完成（模型：{chat_model_name}，消耗：{step5_tokens} tokens）",
                    "duration": step5_duration,
                    "model": chat_model_name,
                    "tokens": step5_tokens
                })
            else:
                # 如果是系统问题，即使没有知识库内容也要回答
                if is_system_question:
                    # 步骤 4: 组合上下文（系统信息）
                    step4_start = time.time()
                    step_data = StepEventData(
                        step=4,
                        title="组合上下文",
                        description="正在准备系统信息作为上下文...",
                        status="in_progress",
                        model=None,
                        tokens=None
                    )
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    await asyncio.sleep(0.3)
                    
                    step4_duration = int((time.time() - step4_start) * 1000)
                    
                    step_data.status = "completed"
                    step_data.description = "上下文准备完成"
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    steps_info.append({
                        "step": 4,
                        "title": "组合上下文",
                        "description": "上下文准备完成",
                        "duration": step4_duration,
                        "model": None,
                        "tokens": None
                    })
                    
                    # 步骤 5: AI 回答
                    step5_start = time.time()
                    step_data = StepEventData(
                        step=5,
                        title="AI 回答",
                        description="正在生成回答...",
                        status="in_progress",
                        model=chat_model_name,
                        tokens=None
                    )
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    # 流式生成 AI 回答
                    full_answer = ""
                    is_first_content = True
                    step5_usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    for text, is_first, is_last, usage_info in ai_client.chat_completion_stream(request.question, context, answer_strategy):
                        if text:
                            full_answer += text
                            content_data = ContentEventData(
                                content=text,
                                is_first=is_first_content,
                                is_last=is_last
                            )
                            yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
                            is_first_content = False
                        if is_last and usage_info:
                            step5_usage_info = usage_info
                    
                    step5_duration = int((time.time() - step5_start) * 1000)
                    
                    # 使用真实的token使用量
                    step5_tokens = step5_usage_info.get("total_tokens", 0)
                    
                    step_data.status = "completed"
                    step_data.description = f"回答生成完成（模型：{chat_model_name}，消耗：{step5_tokens} tokens）"
                    step_data.tokens = step5_tokens
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    steps_info.append({
                        "step": 5,
                        "title": "AI 回答",
                        "description": f"回答生成完成（模型：{chat_model_name}，消耗：{step5_tokens} tokens）",
                        "duration": step5_duration,
                        "model": chat_model_name,
                        "tokens": step5_tokens
                    })
                elif not needs_knowledge_base:
                    # 不需要知识库的普通问题，直接回答
                    # 步骤 4: 直接回答
                    step4_start = time.time()
                    step_data = StepEventData(
                        step=4,
                        title="AI 回答",
                        description="正在生成回答...",
                        status="in_progress",
                        model=chat_model_name,
                        tokens=None
                    )
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    # 流式生成 AI 回答
                    full_answer = ""
                    is_first_content = True
                    step4_usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    for text, is_first, is_last, usage_info in ai_client.chat_completion_stream(request.question, context, answer_strategy):
                        if text:
                            full_answer += text
                            content_data = ContentEventData(
                                content=text,
                                is_first=is_first_content,
                                is_last=is_last
                            )
                            yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
                            is_first_content = False
                        if is_last and usage_info:
                            step4_usage_info = usage_info
                    
                    step4_duration = int((time.time() - step4_start) * 1000)
                    
                    # 使用真实的token使用量
                    step4_tokens = step4_usage_info.get("total_tokens", 0)
                    
                    step_data.status = "completed"
                    step_data.description = f"回答生成完成（模型：{chat_model_name}，消耗：{step4_tokens} tokens）"
                    step_data.tokens = step4_tokens
                    yield f"data: {json.dumps({'type': StreamEventType.STEP, 'data': step_data.model_dump()})}\n\n"
                    
                    steps_info.append({
                        "step": 4,
                        "title": "AI 回答",
                        "description": f"回答生成完成（模型：{chat_model_name}，消耗：{step4_tokens} tokens）",
                        "duration": step4_duration,
                        "model": chat_model_name,
                        "tokens": step4_tokens
                    })
                else:
                    # 需要知识库但没有找到相关内容
                    full_answer = "抱歉，知识库中没有找到与您问题相关的内容，无法回答您的问题。"
                    
                    # 直接发送回答内容
                    content_data = ContentEventData(
                        content=full_answer,
                        is_first=True,
                        is_last=True
                    )
                    yield f"data: {json.dumps({'type': StreamEventType.CONTENT, 'data': content_data.model_dump()})}\n\n"
            
            # 计算结束时间和耗时
            answer_time = get_beijing_time()
            duration = int((time.time() - start_time) * 1000)
            
            # 计算总token数（使用各步骤的真实token使用量）
            total_tokens = step1_tokens + history_compression_tokens
            if 'step2_tokens' in locals():
                total_tokens += step2_tokens
            if 'step3_tokens' in locals():
                total_tokens += step3_tokens
            if 'step4_tokens' in locals():
                total_tokens += step4_tokens
            if 'step5_tokens' in locals():
                total_tokens += step5_tokens
            tokens = total_tokens
            
            # 获取模型名称
            model_name = "unknown"
            try:
                # 从ai_client获取当前使用的模型名称
                config = ai_client.config_service.get_active_config("chat")
                if config:
                    model_name = config.get("model_id", "unknown")
            except Exception:
                pass
            
            # 更新待处理的对话记录
            pending_conversation.question_analysis = question_analysis_result if 'question_analysis_result' in locals() else None
            pending_conversation.answer = full_answer
            pending_conversation.referenced_docs = referenced_docs if referenced_docs else None
            pending_conversation.model = model_name
            pending_conversation.tokens = tokens
            pending_conversation.answer_time = answer_time
            pending_conversation.duration = duration
            pending_conversation.processing_steps = steps_info
            pending_conversation.history_summary = history_summary if conversation_mode == "multi_round" else None
            pending_conversation.status = "completed"
            db.commit()
            
            # 发送完成信号，包含额外信息
            yield f"data: {json.dumps({
                'type': StreamEventType.DONE, 
                'data': {
                    'conversation_id': conversation.id,
                    'conversation_uuid': conversation.conversation_uuid,
                    'model': model_name,
                    'tokens': tokens,
                    'question_time': question_time.isoformat(),
                    'answer_time': answer_time.isoformat(),
                    'duration': duration,
                    'processing_steps': steps_info
                }
            })}\n\n"
            
        except Exception as e:
            db.rollback()
            print(f"Stream chat error: {str(e)}")
            # 更新对话状态为error
            try:
                if 'pending_conversation' in locals():
                    pending_conversation.answer = f"对话失败：{str(e)}"
                    pending_conversation.status = "error"
                    db.commit()
            except Exception as commit_error:
                print(f"Failed to update conversation status: {str(commit_error)}")
            yield f"data: {json.dumps({'type': StreamEventType.ERROR, 'data': {'message': str(e)}})}\n\n"
        finally:
            # 清理活跃对话状态
            if 'conversation_uuid' in locals() and conversation_uuid in active_conversations:
                del active_conversations[conversation_uuid]
    
    headers = {
        "Cache-Control": "no-cache",
        "Transfer-Encoding": "chunked",
        "X-Accel-Buffering": "no",
        "Content-Type": "text/event-stream"
    }
    
    return StreamingResponse(stream_generator(), headers=headers)


@router.post("/chat/stream/stop/{conversation_uuid}")
async def stop_conversation_stream(
    conversation_uuid: UUID,
    current_user: User = Depends(get_current_user)
):
    """终止正在进行的流式对话"""
    conversation_uuid_str = str(conversation_uuid)
    
    # 检查对话是否存在并设置终止标志
    if conversation_uuid_str in active_conversations:
        active_conversations[conversation_uuid_str]["stop"] = True
        return {"success": True, "message": "对话终止请求已发送"}
    
    return {"success": False, "message": "未找到正在进行的对话"}


# AI配置管理

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not (current_user.role == "admin" or getattr(current_user, "is_superuser", False)):
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可访问")
    return current_user


@router.get("/config", response_model=AIConfigResponse)
async def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AI配置"""
    # 获取AI配置
    config = db.query(AIConfig).first()
    
    if not config:
        # 数据库中没有配置，返回空内容
        return AIConfigResponse(
            roleDefinition=RoleDefinition(
                name="",
                description="",
                guidelines=""
            ),
            rules=AIRules(
                answerStrategy="hybrid",
                maxAnswerLength=2000,
                citeSources=True,
                temperature=0.7,
                domains=[]
            ),
            promptTemplates=[]
        )
    
    # 获取角色定义，直接使用数据库中的值
    role_def = config.role_definition or {}
    
    # 获取提示词模板
    templates = db.query(PromptTemplate).filter(PromptTemplate.is_active == 1).all()
    template_responses = [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            type=t.type,
            description=t.description or "",
            content=t.content,
            created_at=t.created_at,
            updated_at=t.updated_at
        ) for t in templates
    ]
    
    return AIConfigResponse(
        roleDefinition=RoleDefinition(
            name=role_def.get("name", ""),
            description=role_def.get("description", ""),
            guidelines=role_def.get("guidelines", "")
        ),
        rules=AIRules(**config.rules),
        promptTemplates=template_responses
    )


@router.put("/config")
async def update_ai_config(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新AI配置（仅管理员）"""
    try:
        config = db.query(AIConfig).first()
        
        if not config:
            # 创建新配置
            config = AIConfig(
                role_definition=request.get("roleDefinition", {}),
                rules=request.get("rules", {})
            )
            db.add(config)
        else:
            # 更新现有配置
            if "roleDefinition" in request:
                config.role_definition = request["roleDefinition"]
            if "rules" in request:
                config.rules = request["rules"]
        
        db.commit()
        
        # 更新提示词模板缓存
        await _update_prompt_templates_cache(db)
        
        return {"success": True, "message": "配置更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/role-definition")
async def update_role_definition(
    request: RoleDefinition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新角色定义（仅管理员）"""
    try:
        config = db.query(AIConfig).first()
        
        if not config:
            # 创建新配置
            config = AIConfig(
                role_definition=request.dict(),
                rules={}
            )
            db.add(config)
        else:
            # 更新角色定义
            config.role_definition = request.dict()
        
        db.commit()
        
        return {"success": True, "message": "角色定义更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/rules")
async def update_rules(
    request: AIRules,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新规则配置（仅管理员）"""
    try:
        config = db.query(AIConfig).first()
        
        if not config:
            # 创建新配置
            config = AIConfig(
                role_definition={},
                rules=request.dict()
            )
            db.add(config)
        else:
            # 更新规则配置
            config.rules = request.dict()
        
        db.commit()
        
        return {"success": True, "message": "规则配置更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompt-templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
    request: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建提示词模板（仅管理员）"""
    try:
        template = PromptTemplate(
            name=request.name,
            type=request.type,
            description=request.description,
            content=request.content
        )
        db.add(template)
        db.commit()
        
        # 更新提示词模板缓存
        await _update_prompt_templates_cache(db)
        
        return PromptTemplateResponse(
            id=template.id,
            name=template.name,
            type=template.type,
            description=template.description or "",
            content=template.content,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: int,
    request: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新提示词模板（仅管理员）"""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    try:
        if request.name is not None:
            template.name = request.name
        if request.type is not None:
            template.type = request.type
        if request.description is not None:
            template.description = request.description
        if request.content is not None:
            template.content = request.content
        
        db.commit()
        
        # 更新提示词模板缓存
        await _update_prompt_templates_cache(db)
        
        return PromptTemplateResponse(
            id=template.id,
            name=template.name,
            type=template.type,
            description=template.description or "",
            content=template.content,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除提示词模板（仅管理员）"""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    try:
        template.is_active = 0
        db.commit()
        
        # 更新提示词模板缓存
        await _update_prompt_templates_cache(db)
        
        return {"success": True, "message": "模板删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def _update_prompt_templates_cache(db: Session):
    """更新提示词模板缓存"""
    templates = db.query(PromptTemplate).filter(PromptTemplate.is_active == 1).all()
    
    template_dict = {}
    for template in templates:
        # 根据模板类型生成缓存键
        if template.type == "role":
            template_dict["role"] = template.content
        elif template.type == "rule":
            # 规则类型需要根据策略类型进一步分类
            # 这里简单处理，将所有规则类型合并
            if "rule_based_rule" not in template_dict:
                template_dict["rule_based_rule"] = template.content
            else:
                template_dict["rule_based_rule"] += "\n\n" + template.content
        elif template.type == "format":
            template_dict["format"] = template.content
        else:
            # 其他类型作为知识基础规则
            if "knowledge_base_rule" not in template_dict:
                template_dict["knowledge_base_rule"] = template.content
            else:
                template_dict["knowledge_base_rule"] += "\n\n" + template.content
    
    # 更新全局提示词模板缓存
    global prompt_templates_cache
    prompt_templates_cache = template_dict
