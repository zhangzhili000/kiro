import asyncio
import json
import os
import threading
from typing import Optional
from datetime import datetime
from kiro.core.timezone_utils import get_beijing_time
from kiro.core.config import settings
from kiro.core.database import SessionLocal
from kiro.models.document import Document
from kiro.services.model_service import DynamicAIClient
from kiro.services.ai_service import faiss_service


class AsyncTaskService:
    """异步任务服务"""
    
    def __init__(self):
        self.tasks = {}  # 存储正在运行的任务 {document_id: task}
        self.index_status = {}  # 存储索引状态 {document_id: {'status': '', 'progress': 0, 'message': ''}}
    
    def create_document_index(self, document_id: int):
        """异步创建文档索引"""
        # 设置初始状态
        self.index_status[document_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '正在生成索引...',
            'updated_at': get_beijing_time().isoformat()
        }
        
        # 使用线程来运行异步任务，避免需要运行的事件循环
        thread = threading.Thread(target=self._run_index_task, args=(document_id,), daemon=True)
        thread.start()
        self.tasks[document_id] = thread
    
    def _run_index_task(self, document_id: int):
        """在新线程中运行索引任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._process_index(document_id))
        loop.close()
    
    async def _process_index(self, document_id: int):
        """处理索引生成的实际逻辑"""
        try:
            # 获取文档内容
            db = SessionLocal()
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                self.index_status[document_id] = {
                    'status': 'failed',
                    'progress': 0,
                    'message': '文档不存在',
                    'updated_at': get_beijing_time().isoformat(),
                    'chunk_count': 0
                }
                db.close()
                return
            
            # 创建动态AI客户端
            ai_client = DynamicAIClient(db)
            
            # 步骤1: 提取关键词
            self.index_status[document_id] = {
                'status': 'processing',
                'progress': 25,
                'message': '正在提取关键词...',
                'updated_at': get_beijing_time().isoformat()
            }
            
            try:
                keywords = ai_client.extract_keywords(document.content or document.title, top_k=10)
                document.keywords = keywords
            except Exception as e:
                print(f"DEBUG: 关键词提取失败: {str(e)}")
                document.keywords = []
            
            # 步骤2: 生成摘要
            self.index_status[document_id] = {
                'status': 'processing',
                'progress': 50,
                'message': '正在生成摘要...',
                'updated_at': get_beijing_time().isoformat()
            }
            
            try:
                summary = ai_client.get_summary(document.content or document.title, max_length=300)
                document.summary = summary
            except Exception as e:
                print(f"DEBUG: 摘要生成失败: {str(e)}")
                document.summary = ""
            
            # 步骤3: 生成向量并添加到索引
            self.index_status[document_id] = {
                'status': 'processing',
                'progress': 75,
                'message': '正在生成向量索引...',
                'updated_at': get_beijing_time().isoformat()
            }
            
            try:
                content_for_embedding = f"{document.title}\n\n{document.content}" if document.content else document.title
                
                # 将文档切分成chunk（每500字符一个chunk）
                chunks = []
                if document.content and len(document.content) > 0:
                    chunk_size = 500
                    for i in range(0, len(document.content), chunk_size):
                        chunk_content = document.content[i:i + chunk_size]
                        chunks.append({
                            "document_id": document.id,
                            "document_title": document.title,
                            "chunk_index": len(chunks),
                            "chunk_content": chunk_content,
                            "title": document.title,
                            "content": chunk_content,
                            "category_id": document.category_id,
                            "author_id": document.author_id
                        })
                else:
                    # 如果没有内容，至少添加一个chunk
                    chunks.append({
                        "document_id": document.id,
                        "document_title": document.title,
                        "chunk_index": 0,
                        "chunk_content": document.title,
                        "title": document.title,
                        "content": document.title,
                        "category_id": document.category_id,
                        "author_id": document.author_id
                    })
                
                # 为每个chunk生成embedding
                embeddings = []
                for chunk in chunks:
                    chunk_text = f"{chunk['document_title']}\n\n{chunk['chunk_content']}"
                    embedding = ai_client.get_embedding(chunk_text)
                    embeddings.append(embedding)
                
                # 添加到索引
                faiss_service.add_vectors(embeddings, chunks)
                faiss_service.save_index()
                
                chunk_count = len(chunks)
                
            except Exception as e:
                print(f"DEBUG: 向量索引失败: {str(e)}")
                chunk_count = 0
            
            # 更新文档状态
            document.status = "published"
            db.commit()
            
            # 完成
            self.index_status[document_id] = {
                'status': 'completed',
                'progress': 100,
                'message': '索引生成完成',
                'updated_at': get_beijing_time().isoformat(),
                'chunk_count': chunk_count
            }
            
            db.close()
            
        except Exception as e:
            print(f"DEBUG: 索引生成任务失败: {str(e)}")
            self.index_status[document_id] = {
                'status': 'failed',
                'progress': 0,
                'message': f'索引生成失败: {str(e)}',
                'updated_at': get_beijing_time().isoformat(),
                'chunk_count': 0
            }
        
        finally:
            # 清理任务
            if document_id in self.tasks:
                del self.tasks[document_id]
    
    def get_index_status(self, document_id: int) -> Optional[dict]:
        """获取文档索引状态"""
        status = self.index_status.get(document_id)
        
        # 如果状态不存在，检查文档是否已发布
        if status is None:
            db = SessionLocal()
            document = db.query(Document).filter(Document.id == document_id).first()
            db.close()
            
            if document and document.status == "published":
                # 从FAISS索引中统计该文档的chunk数量
                chunk_count = 0
                try:
                    for doc in faiss_service.documents:
                        if str(doc.get("document_id")) == str(document_id):
                            chunk_count += 1
                except Exception as e:
                    print(f"DEBUG: 统计chunk数量失败: {str(e)}")
                
                return {
                    'status': 'completed',
                    'progress': 100,
                    'message': '索引已生成',
                    'updated_at': document.updated_at.isoformat() if document.updated_at else get_beijing_time().isoformat(),
                    'chunk_count': chunk_count
                }
            elif document and document.status == "draft":
                return {
                    'status': 'pending',
                    'progress': 0,
                    'message': '等待索引生成',
                    'updated_at': get_beijing_time().isoformat(),
                    'chunk_count': 0
                }
        
        return status
    
    def cancel_task(self, document_id: int):
        """取消正在进行的索引任务"""
        task = self.tasks.get(document_id)
        if task and not task.done():
            task.cancel()
            self.index_status[document_id] = {
                'status': 'cancelled',
                'progress': 0,
                'message': '任务已取消',
                'updated_at': get_beijing_time().isoformat()
            }
            del self.tasks[document_id]


async_task_service = AsyncTaskService()
