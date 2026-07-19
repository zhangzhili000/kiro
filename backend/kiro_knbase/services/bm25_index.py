"""
BM25 关键词检索引擎

提供基于 BM25 算法的关键词检索能力，作为向量检索的补充，
实现多路召回，提高知识库的召回率。

主要功能：
- 构建文档倒排索引
- BM25 相关性计算
- 关键词检索
- 与向量检索结果合并
"""
import re
import math
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 尝试导入 jieba 分词，如果没有则使用简单分词
try:
    import jieba
    HAS_JIEBA = True
    # 开启新词发现模式（可选）
    jieba.initialize()
except ImportError:
    HAS_JIEBA = False
    logger.warning("jieba not installed, using simple tokenizer")


@dataclass
class BM25Document:
    """
    BM25 文档
    
    存储文档的分词结果和元数据。
    """
    doc_id: str  # 文档唯一标识（如 "doc_7_chunk_2"）
    document_id: int  # 文档 ID
    chunk_index: int  # 块索引
    title: str  # 文档标题
    content: str  # 文档内容
    tokens: List[str] = field(default_factory=list)  # 分词结果
    token_freq: Dict[str, int] = field(default_factory=dict)  # 词频
    doc_len: int = 0  # 文档长度

    def to_dict(self) -> Dict[str, any]:
        """转换为字典"""
        return {
            "doc_id": self.doc_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "content": self.content,
            "doc_len": self.doc_len,
        }


class BM25Index:
    """
    BM25 索引
    
    基于 BM25 算法的关键词检索引擎。
    
    BM25 公式：
    score(D, Q) = Σ IDF(qi) * f(qi, D) * (k1 + 1) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))
    
    其中：
    - D: 文档
    - Q: 查询
    - qi: 查询词
    - f(qi, D): 词 qi 在文档 D 中的词频
    - |D|: 文档长度
    - avgdl: 平均文档长度
    - k1, b: 超参数（通常 k1=1.2~2.0, b=0.75）
    - IDF: 逆文档频率
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        use_jieba: bool = True
    ):
        """
        初始化 BM25 索引
        
        Args:
            k1: BM25 的 k1 参数（控制词频饱和），默认 1.5
            b: BM25 的 b 参数（控制文档长度归一化），默认 0.75
            use_jieba: 是否使用 jieba 分词（仅中文有效）
        """
        self.k1 = k1
        self.b = b
        self.use_jieba = use_jieba and HAS_JIEBA
        
        # 文档集合
        self.docs: Dict[str, BM25Document] = {}
        
        # 倒排索引 {term: [(doc_id, freq), ...]}
        self.inverted_index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        
        # 文档频率 {term: doc_count}
        self.df: Dict[str, int] = defaultdict(int)
        
        # IDF 值缓存
        self.idf_cache: Dict[str, float] = {}
        
        # 平均文档长度
        self.avgdl: float = 0.0
        
        # 总文档数
        self.total_docs: int = 0
        
        # 停用词（中文常见停用词）
        self.stop_words = self._load_stop_words()

    # ============== 分词相关 ==============

    def _load_stop_words(self) -> set:
        """加载停用词表"""
        # 基础停用词
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
            '为', '因为', '所以', '但是', '而且', '或者', '如果', '虽然', '然后', '可以',
            '能', '能够', '应该', '必须', '需要', '把', '被', '让', '使', '将',
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'shall', 'should', 'may', 'might', 'can', 'could',
            'this', 'that', 'these', 'those', 'it', 'its', 'of', 'in', 'on',
            'at', 'by', 'for', 'with', 'about', 'from', 'to',
        }
        return stop_words

    def tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词
        
        Args:
            text: 文本内容
            
        Returns:
            分词结果列表
        """
        if not text or not text.strip():
            return []
        
        if self.use_jieba:
            return self._tokenize_with_jieba(text)
        else:
            return self._tokenize_simple(text)

    def _tokenize_with_jieba(self, text: str) -> List[str]:
        """使用 jieba 分词"""
        # 先按句子分割，再分词（提高效率）
        sentences = re.split(r'[。！？.!?；;\n]', text)
        tokens = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # 使用 jieba 精确模式分词
            words = jieba.lcut(sentence, cut_all=False)
            # 过滤停用词和短词
            for word in words:
                word = word.strip().lower()
                if word and len(word) >= 2 and word not in self.stop_words:
                    tokens.append(word)
        
        return tokens

    def _tokenize_simple(self, text: str) -> List[str]:
        """简单分词（按空格和标点分割）"""
        # 英文按空格分词
        if re.match(r'^[a-zA-Z\s\W]+$', text):
            words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
            return [w for w in words if w not in self.stop_words]
        
        # 中文使用 n-gram
        tokens = []
        # 提取中文词组（2-4字）
        for n in [2, 3, 4]:
            for i in range(len(text) - n + 1):
                gram = text[i:i+n]
                # 检查是否主要是中文
                if re.match(r'^[\u4e00-\u9fa5]+$', gram):
                    tokens.append(gram)
        
        return tokens

    # ============== 索引构建 ==============

    def add_document(
        self,
        doc_id: str,
        content: str,
        title: str = "",
        document_id: int = 0,
        chunk_index: int = 0
    ) -> bool:
        """
        添加文档到索引
        
        Args:
            doc_id: 文档唯一标识
            content: 文档内容
            title: 文档标题
            document_id: 文档 ID
            chunk_index: 块索引
            
        Returns:
            是否添加成功
        """
        try:
            # 标题和内容一起分词（标题权重更高，但这里先简单合并）
            full_text = f"{title}\n{content}"
            
            # 分词
            tokens = self.tokenize(full_text)
            
            if not tokens:
                # 没有有效分词，跳过
                return False
            
            # 计算词频
            token_freq: Dict[str, int] = defaultdict(int)
            for token in tokens:
                token_freq[token] += 1
            
            # 创建文档对象
            doc = BM25Document(
                doc_id=doc_id,
                document_id=document_id,
                chunk_index=chunk_index,
                title=title,
                content=content,
                tokens=tokens,
                token_freq=dict(token_freq),
                doc_len=len(tokens)
            )
            
            # 如果文档已存在，先删除旧的
            if doc_id in self.docs:
                self.remove_document(doc_id)
            
            # 添加到文档集合
            self.docs[doc_id] = doc
            
            # 更新倒排索引和文档频率
            for term, freq in token_freq.items():
                self.inverted_index[term].append((doc_id, freq))
                self.df[term] += 1
            
            # 更新统计信息
            self.total_docs = len(self.docs)
            self._recalculate_avgdl()
            
            # 清除 IDF 缓存
            self.idf_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to BM25 index: {e}")
            return False

    def remove_document(self, doc_id: str) -> bool:
        """
        从索引中删除文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            是否删除成功
        """
        if doc_id not in self.docs:
            return False
        
        try:
            doc = self.docs[doc_id]
            
            # 从倒排索引中移除
            for term, freq in doc.token_freq.items():
                if term in self.inverted_index:
                    self.inverted_index[term] = [
                        (did, f) for did, f in self.inverted_index[term]
                        if did != doc_id
                    ]
                    if not self.inverted_index[term]:
                        del self.inverted_index[term]
                    self.df[term] -= 1
                    if self.df[term] <= 0:
                        del self.df[term]
            
            # 从文档集合中移除
            del self.docs[doc_id]
            
            # 更新统计信息
            self.total_docs = len(self.docs)
            self._recalculate_avgdl()
            
            # 清除 IDF 缓存
            self.idf_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove document from BM25 index: {e}")
            return False

    def _recalculate_avgdl(self):
        """重新计算平均文档长度"""
        if self.total_docs == 0:
            self.avgdl = 0.0
            return
        
        total_len = sum(doc.doc_len for doc in self.docs.values())
        self.avgdl = total_len / self.total_docs

    # ============== 检索相关 ==============

    def search(
        self,
        query: str,
        top_k: int = 20,
        min_score: float = 0.0
    ) -> List[Dict[str, any]]:
        """
        BM25 检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_score: 最低分数阈值
            
        Returns:
            检索结果列表，按分数降序排列
        """
        if not query or not query.strip():
            return []
        
        if self.total_docs == 0:
            return []
        
        # 对查询进行分词
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        # 计算每个文档的得分
        scores: Dict[str, float] = defaultdict(float)
        
        for term in query_tokens:
            if term not in self.df:
                continue
            
            # 计算 IDF
            idf = self._get_idf(term)
            
            # 遍历包含该词的文档
            for doc_id, freq in self.inverted_index.get(term, []):
                doc = self.docs.get(doc_id)
                if not doc:
                    continue
                
                # BM25 得分计算
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc.doc_len / self.avgdl) if self.avgdl > 0 else freq + self.k1
                tf_component = numerator / denominator
                
                scores[doc_id] += idf * tf_component
        
        # 按得分排序
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 构建结果
        results = []
        for doc_id, score in sorted_docs:
            if score < min_score:
                continue
            
            doc = self.docs.get(doc_id)
            if not doc:
                continue
            
            result = doc.to_dict()
            result["bm25_score"] = score
            result["score"] = score  # 兼容字段
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results

    def _get_idf(self, term: str) -> float:
        """
        计算词的 IDF（逆文档频率）
        
        使用 BM25+ 的 IDF 公式，避免负 IDF：
        IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        n = self.df.get(term, 0)
        N = self.total_docs
        
        # BM25+ IDF 公式，避免负值
        idf = math.log((N - n + 0.5) / (n + 0.5) + 1.0)
        
        self.idf_cache[term] = idf
        return idf

    # ============== 工具方法 ==============

    def get_stats(self) -> Dict[str, any]:
        """获取索引统计信息"""
        return {
            "total_docs": self.total_docs,
            "avg_doc_length": self.avgdl,
            "vocab_size": len(self.df),
            "k1": self.k1,
            "b": self.b,
        }

    def clear(self):
        """清空索引"""
        self.docs.clear()
        self.inverted_index.clear()
        self.df.clear()
        self.idf_cache.clear()
        self.avgdl = 0.0
        self.total_docs = 0

    def is_empty(self) -> bool:
        """索引是否为空"""
        return self.total_docs == 0


# 全局单例
_bm25_index: Optional[BM25Index] = None


def get_bm25_index() -> BM25Index:
    """获取 BM25 索引单例"""
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index()
    return _bm25_index


__all__ = [
    "BM25Document",
    "BM25Index",
    "get_bm25_index",
]
