"""
知识检索服务（Retrieval Service）

提供统一的知识检索接口，实现多路召回和混合排序：
- 向量召回（FAISS）
- 关键词召回（BM25）
- 混合排序（综合向量分和关键词分）
- 动态阈值与保底返回
"""
import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from kiro_platform.core.config import settings
from kiro_knbase.services.ai_service import faiss_service
from kiro_knbase.services.bm25_index import get_bm25_index

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """
    检索结果
    
    封装单个检索结果，包含内容、相似度、来源等信息。
    """
    document_id: int  # 文档 ID
    document_title: str  # 文档标题
    chunk_index: int  # 块索引
    chunk_content: str  # 块内容
    
    # 相似度分数
    vector_score: float = 0.0  # 向量相似度（余弦相似度，0-1）
    bm25_score: float = 0.0  # BM25 分数
    final_score: float = 0.0  # 最终综合分数
    
    # 元数据
    section_path: List[str] = field(default_factory=list)  # 章节路径
    headings: List[str] = field(default_factory=list)  # 所属标题
    page_number: Optional[int] = None  # 页码
    chunk_type: str = "text"  # 块类型
    
    # 来源信息
    sources: List[str] = field(default_factory=list)  # 召回来源（vector/bm25）
    confidence: str = "medium"  # 置信度（high/medium/low）

    def to_dict(self) -> Dict[str, any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_index": self.chunk_index,
            "chunk_content": self.chunk_content,
            "content": self.chunk_content,
            "title": self.document_title,
            "similarity": self.final_score,
            "distance": self.final_score,
            "vector_score": self.vector_score,
            "bm25_score": self.bm25_score,
            "final_score": self.final_score,
            "section_path": self.section_path,
            "headings": self.headings,
            "page_number": self.page_number,
            "chunk_type": self.chunk_type,
            "sources": self.sources,
            "confidence": self.confidence,
        }


class RetrievalService:
    """
    知识检索服务
    
    提供统一的检索接口，支持多路召回和混合排序。
    """

    def __init__(
        self,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        similarity_threshold: float = 0.6,
        min_return_count: int = 3,
        max_return_count: int = 15,
        enable_bm25: bool = True
    ):
        """
        初始化检索服务
        
        Args:
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            similarity_threshold: 相似度阈值（低于阈值的结果被过滤，但保底返回不受此限制）
            min_return_count: 最少返回结果数（保底返回）
            max_return_count: 最多返回结果数
            enable_bm25: 是否启用 BM25 关键词检索
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.similarity_threshold = similarity_threshold
        self.min_return_count = min_return_count
        self.max_return_count = max_return_count
        self.enable_bm25 = enable_bm25
        
        self.faiss = faiss_service
        self.bm25 = get_bm25_index()

    def search(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 15,
        accessible_doc_ids: Optional[set] = None
    ) -> List[RetrievalResult]:
        """
        统一检索入口
        
        执行多路召回，混合排序，返回最终结果。
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回结果数量
            accessible_doc_ids: 有权限访问的文档 ID 集合（None 表示不过滤）
            
        Returns:
            检索结果列表，按相关度降序排列
        """
        start_time = time.time()
        
        # 1. 多路召回
        vector_results = self._vector_search(query_vector, top_k * 2)
        bm25_results = []
        if self.enable_bm25 and not self.bm25.is_empty():
            bm25_results = self._bm25_search(query, top_k * 2)
        
        logger.debug(
            f"Retrieval: vector={len(vector_results)} results, "
            f"bm25={len(bm25_results)} results"
        )
        
        # 2. 合并去重
        merged_results = self._merge_results(vector_results, bm25_results)
        
        # 3. 权限过滤
        if accessible_doc_ids is not None:
            merged_results = [
                r for r in merged_results
                if str(r.document_id) in accessible_doc_ids
            ]
        
        # 4. 排序
        merged_results.sort(key=lambda r: r.final_score, reverse=True)
        
        # 5. 动态阈值过滤 + 保底返回
        final_results = self._apply_dynamic_threshold(merged_results, top_k)
        
        elapsed = int((time.time() - start_time) * 1000)
        logger.info(
            f"Retrieval completed: query='{query[:30]}...', "
            f"results={len(final_results)}, time={elapsed}ms"
        )
        
        return final_results

    # ============== 召回策略 ==============

    def _vector_search(
        self,
        query_vector: List[float],
        top_k: int
    ) -> List[Dict[str, any]]:
        """向量检索"""
        try:
            results = self.faiss.search(query_vector, top_k=top_k)
            # 标记来源
            for r in results:
                r["_source"] = "vector"
                r["_vector_score"] = r.get("similarity", 0.0)
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _bm25_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, any]]:
        """BM25 关键词检索"""
        try:
            results = self.bm25.search(query, top_k=top_k)
            # 标记来源
            for r in results:
                r["_source"] = "bm25"
                r["_bm25_score"] = r.get("bm25_score", 0.0)
            return results
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    # ============== 结果合并与排序 ==============

    def _merge_results(
        self,
        vector_results: List[Dict[str, any]],
        bm25_results: List[Dict[str, any]]
    ) -> List[RetrievalResult]:
        """
        合并多路召回结果
        
        使用文档唯一标识（doc_id = document_id_chunk_index）作为 key 去重。
        """
        merged: Dict[str, RetrievalResult] = {}
        
        # 归一化 BM25 分数（缩放到 0-1 范围）
        max_bm25 = max((r.get("_bm25_score", 0) for r in bm25_results), default=1.0)
        if max_bm25 == 0:
            max_bm25 = 1.0
        
        # 处理向量结果
        for r in vector_results:
            doc_id = f"{r.get('document_id')}_{r.get('chunk_index', 0)}"
            
            if doc_id not in merged:
                merged[doc_id] = RetrievalResult(
                    document_id=int(r.get("document_id", 0)),
                    document_title=r.get("document_title", r.get("title", "")),
                    chunk_index=int(r.get("chunk_index", 0)),
                    chunk_content=r.get("chunk_content", r.get("content", "")),
                    vector_score=r.get("similarity", r.get("_vector_score", 0.0)),
                    section_path=r.get("section_path", []),
                    headings=r.get("headings", []),
                    page_number=r.get("page_number"),
                    chunk_type=r.get("chunk_type", "text"),
                    sources=["vector"],
                )
            else:
                # 已存在（说明 BM25 也召回了）
                merged[doc_id].vector_score = r.get("similarity", r.get("_vector_score", 0.0))
                if "vector" not in merged[doc_id].sources:
                    merged[doc_id].sources.append("vector")
        
        # 处理 BM25 结果
        for r in bm25_results:
            doc_id = f"{r.get('document_id')}_{r.get('chunk_index', 0)}"
            
            # 归一化 BM25 分数
            normalized_bm25 = r.get("_bm25_score", 0.0) / max_bm25
            
            if doc_id not in merged:
                merged[doc_id] = RetrievalResult(
                    document_id=int(r.get("document_id", 0)),
                    document_title=r.get("title", ""),
                    chunk_index=int(r.get("chunk_index", 0)),
                    chunk_content=r.get("content", ""),
                    bm25_score=normalized_bm25,
                    sources=["bm25"],
                )
            else:
                # 已存在（向量也召回了）
                merged[doc_id].bm25_score = normalized_bm25
                if "bm25" not in merged[doc_id].sources:
                    merged[doc_id].sources.append("bm25")
        
        # 计算最终综合分数
        results = list(merged.values())
        for r in results:
            r.final_score = self._calculate_final_score(r)
            r.confidence = self._calculate_confidence(r.final_score)
        
        return results

    def _calculate_final_score(self, result: RetrievalResult) -> float:
        """
        计算最终综合分数
        
        加权平均：
        final = vector_weight * vector_score + bm25_weight * bm25_score
        
        如果只有一个来源，则使用该来源的分数。
        """
        has_vector = "vector" in result.sources
        has_bm25 = "bm25" in result.sources
        
        if has_vector and has_bm25:
            # 两个来源都有，加权平均
            return (
                self.vector_weight * result.vector_score
                + self.bm25_weight * result.bm25_score
            )
        elif has_vector:
            # 只有向量
            return result.vector_score
        elif has_bm25:
            # 只有 BM25（适当降低权重，因为单一召回来源）
            return result.bm25_score * 0.8
        else:
            return 0.0

    def _calculate_confidence(self, score: float) -> str:
        """根据分数计算置信度"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"

    # ============== 动态阈值 ==============

    def _apply_dynamic_threshold(
        self,
        results: List[RetrievalResult],
        top_k: int
    ) -> List[RetrievalResult]:
        """
        应用动态阈值和保底返回策略
        
        策略：
        1. 优先返回相似度 >= 阈值的结果
        2. 如果结果数不足保底数量，则返回 Top N（N = min_return_count）
        3. 最多返回 max_return_count 个结果
        """
        if not results:
            return []
        
        # 限制最大返回数
        max_count = min(top_k, self.max_return_count)
        
        # 先过滤出高于阈值的结果
        above_threshold = [r for r in results if r.final_score >= self.similarity_threshold]
        
        if len(above_threshold) >= self.min_return_count:
            # 高于阈值的结果足够，直接返回
            return above_threshold[:max_count]
        else:
            # 高于阈值的结果不足，保底返回 min_return_count 个
            # （即使低于阈值也返回，但会标记低置信度）
            return results[:min(max_count, self.min_return_count)]

    # ============== BM25 索引管理 ==============

    def add_to_bm25_index(
        self,
        document_id: int,
        chunk_index: int,
        title: str,
        content: str
    ):
        """添加文档块到 BM25 索引"""
        if not self.enable_bm25:
            return
        
        doc_id = f"{document_id}_{chunk_index}"
        self.bm25.add_document(
            doc_id=doc_id,
            content=content,
            title=title,
            document_id=document_id,
            chunk_index=chunk_index,
        )

    def remove_from_bm25_index(self, document_id: int):
        """从 BM25 索引中删除文档的所有块"""
        if not self.enable_bm25:
            return
        
        # 找出所有属于该文档的块并删除
        to_remove = [
            doc_id for doc_id in self.bm25.docs
            if self.bm25.docs[doc_id].document_id == document_id
        ]
        for doc_id in to_remove:
            self.bm25.remove_document(doc_id)

    def get_retrieval_stats(self) -> Dict[str, any]:
        """获取检索统计信息"""
        return {
            "bm25_enabled": self.enable_bm25,
            "bm25_stats": self.bm25.get_stats() if self.enable_bm25 else {},
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "similarity_threshold": self.similarity_threshold,
            "min_return_count": self.min_return_count,
            "max_return_count": self.max_return_count,
        }


# 全局单例
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """获取检索服务单例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


__all__ = [
    "RetrievalResult",
    "RetrievalService",
    "get_retrieval_service",
]
