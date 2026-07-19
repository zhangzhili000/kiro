"""
文档分块器（Document Chunker）

提供多种文档分块策略，用于将文档内容切分为适合向量化的语义块。

支持的分块策略：
1. 基于标题层级的语义分块（推荐，适用于有结构的文档）
2. 基于段落的分块（默认，适用于一般文档）
3. 基于固定大小的分块（兼容旧版本）
4. 递归分块（适用于长文档）

每个分块包含丰富的元数据：
- 文档信息（ID、标题）
- 位置信息（块索引、页码）
- 结构信息（所属章节、标题路径）
- 内容信息（块内容、块类型）
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """
    文档块
    
    表示一个被切分后的文档块，包含内容和元数据。
    """
    # 内容
    content: str  # 块内容
    
    # 文档信息
    document_id: Optional[int] = None  # 文档 ID
    document_title: str = ""  # 文档标题
    
    # 位置信息
    chunk_index: int = 0  # 块索引
    page_number: Optional[int] = None  # 页码
    start_pos: int = 0  # 在原文中的起始位置
    end_pos: int = 0  # 在原文中的结束位置
    
    # 结构信息
    section_path: List[str] = field(default_factory=list)  # 章节路径（标题层级）
    headings: List[str] = field(default_factory=list)  # 所属标题列表
    
    # 类型信息
    chunk_type: str = "text"  # 块类型：text/table/image/caption
    is_heading: bool = False  # 是否为标题块
    
    # 元数据
    metadata: Dict[str, any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> Dict[str, any]:
        """转换为字典（用于 FAISS 索引存储）"""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_index": self.chunk_index,
            "chunk_content": self.content,
            "content": self.content,
            "title": self.document_title,
            "page_number": self.page_number,
            "section_path": self.section_path,
            "headings": self.headings,
            "chunk_type": self.chunk_type,
            "is_heading": self.is_heading,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            **self.metadata
        }


class DocumentChunker:
    """
    文档分块器
    
    提供多种分块策略，将文档内容切分为语义块。
    """

    def __init__(
        self,
        max_chunk_size: int = 600,
        min_chunk_size: int = 100,
        chunk_overlap: float = 0.15,
        use_semantic_chunking: bool = True
    ):
        """
        初始化分块器
        
        Args:
            max_chunk_size: 最大块大小（字符数）
            min_chunk_size: 最小块大小（字符数）
            chunk_overlap: 块之间的重叠比例（0-1）
            use_semantic_chunking: 是否使用语义分块
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_semantic_chunking = use_semantic_chunking

    def chunk_document(
        self,
        content: str,
        document_title: str = "",
        document_id: Optional[int] = None,
        file_type: str = "md",
        metadata: Optional[Dict[str, any]] = None
    ) -> List[DocumentChunk]:
        """
        对文档进行分块
        
        Args:
            content: 文档内容
            document_title: 文档标题
            document_id: 文档 ID
            file_type: 文件类型（md/pdf/docx/txt）
            metadata: 额外元数据
            
        Returns:
            分块后的文档块列表
        """
        if not content or not content.strip():
            # 空内容，返回一个标题块
            chunk = DocumentChunk(
                content=document_title,
                document_id=document_id,
                document_title=document_title,
                chunk_index=0,
                chunk_type="text",
                metadata=metadata or {}
            )
            return [chunk]

        # 根据文件类型选择分块策略
        if self.use_semantic_chunking and file_type in ["md", "markdown"]:
            chunks = self._chunk_by_headings(
                content, document_title, document_id, metadata
            )
        elif self.use_semantic_chunking and file_type in ["pdf", "docx"]:
            # 对于 PDF/DOCX，尝试按段落分块，同时检测标题
            chunks = self._chunk_by_paragraphs_with_heading_detection(
                content, document_title, document_id, metadata
            )
        else:
            # 默认：按段落分块
            chunks = self._chunk_by_paragraphs(
                content, document_title, document_id, metadata
            )

        # 确保块大小在合理范围内
        chunks = self._normalize_chunks(chunks)

        # 分配块索引
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i

        logger.info(f"Document chunked into {len(chunks)} chunks (title: {document_title})")
        return chunks

    # ============== 分块策略实现 ==============

    def _chunk_by_headings(
        self,
        content: str,
        document_title: str,
        document_id: Optional[int],
        metadata: Optional[Dict[str, any]]
    ) -> List[DocumentChunk]:
        """
        基于标题层级的语义分块（适用于 Markdown 文档）
        
        策略：
        1. 按标题（# 到 ######）切分文档
        2. 每个标题下的内容作为一个或多个块
        3. 保留标题路径（如 ["第一章", "1.1 节"]）
        4. 内容过长时按段落进一步切分
        """
        chunks = []
        # 当前标题栈（用于构建 section_path）
        heading_stack: List[Tuple[int, str]] = []  # (level, text)

        # 按行遍历，识别标题和内容
        lines = content.split("\n")
        current_section_content = []
        current_section_start_line = 0

        def _flush_section(end_line: int):
            """将当前章节内容刷新为块"""
            nonlocal current_section_content, current_section_start_line
            
            section_text = "\n".join(current_section_content).strip()
            if not section_text:
                return

            # 构建标题路径
            section_path = [h[1] for h in heading_stack]
            
            # 如果内容过长，按段落进一步切分
            if len(section_text) > self.max_chunk_size:
                sub_chunks = self._split_text_into_chunks(
                    section_text,
                    max_size=self.max_chunk_size,
                    overlap=int(self.max_chunk_size * self.chunk_overlap)
                )
                for sub_content in sub_chunks:
                    chunk = DocumentChunk(
                        content=sub_content,
                        document_id=document_id,
                        document_title=document_title,
                        section_path=section_path.copy(),
                        headings=section_path.copy(),
                        chunk_type="text",
                        metadata=metadata or {}
                    )
                    chunks.append(chunk)
            else:
                chunk = DocumentChunk(
                    content=section_text,
                    document_id=document_id,
                    document_title=document_title,
                    section_path=section_path.copy(),
                    headings=section_path.copy(),
                    chunk_type="text",
                    metadata=metadata or {}
                )
                chunks.append(chunk)
            
            current_section_content = []

        for i, line in enumerate(lines):
            # 检测 Markdown 标题
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            
            if heading_match:
                # 先刷新当前章节
                _flush_section(i)
                
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                # 更新标题栈（弹出同级及更深的标题）
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading_text))
                
                # 标题本身也作为一个块（可选，用于提高标题匹配的召回率）
                # 暂时不添加标题块，避免重复
            else:
                current_section_content.append(line)

        # 处理最后一个章节
        _flush_section(len(lines))

        # 如果没有识别到任何标题，回退到段落分块
        if not chunks:
            return self._chunk_by_paragraphs(
                content, document_title, document_id, metadata
            )

        return chunks

    def _chunk_by_paragraphs_with_heading_detection(
        self,
        content: str,
        document_title: str,
        document_id: Optional[int],
        metadata: Optional[Dict[str, any]]
    ) -> List[DocumentChunk]:
        """
        按段落分块，并尝试检测标题（适用于 PDF/DOCX 解析后的文本）
        
        标题检测规则：
        - 短文本行（<50字）
        - 以数字开头（如 "1. ", "1.1 "）
        - 全大写或首字母大写
        - 前后有空行
        """
        paragraphs = self._split_into_paragraphs(content)
        chunks = []
        current_chunk_parts = []
        current_section_path = []
        current_chunk_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检测是否为标题
            is_heading = self._detect_heading(para)
            
            if is_heading:
                # 先刷新当前块
                if current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunk = DocumentChunk(
                        content=chunk_text,
                        document_id=document_id,
                        document_title=document_title,
                        section_path=current_section_path.copy(),
                        headings=current_section_path.copy(),
                        chunk_type="text",
                        metadata=metadata or {}
                    )
                    chunks.append(chunk)
                    current_chunk_parts = []
                    current_chunk_size = 0
                
                # 更新章节路径（简化处理，直接替换）
                current_section_path = [para]
            
            # 判断是否需要新建块
            para_size = len(para)
            if current_chunk_size + para_size > self.max_chunk_size and current_chunk_parts:
                # 当前块已满，新建块
                chunk_text = "\n\n".join(current_chunk_parts)
                chunk = DocumentChunk(
                    content=chunk_text,
                    document_id=document_id,
                    document_title=document_title,
                    section_path=current_section_path.copy(),
                    headings=current_section_path.copy(),
                    chunk_type="text",
                    metadata=metadata or {}
                )
                chunks.append(chunk)
                current_chunk_parts = [para]
                current_chunk_size = para_size
            else:
                current_chunk_parts.append(para)
                current_chunk_size += para_size

        # 处理最后一个块
        if current_chunk_parts:
            chunk_text = "\n\n".join(current_chunk_parts)
            chunk = DocumentChunk(
                content=chunk_text,
                document_id=document_id,
                document_title=document_title,
                section_path=current_section_path.copy(),
                headings=current_section_path.copy(),
                chunk_type="text",
                metadata=metadata or {}
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_paragraphs(
        self,
        content: str,
        document_title: str,
        document_id: Optional[int],
        metadata: Optional[Dict[str, any]]
    ) -> List[DocumentChunk]:
        """
        按段落分块（基础分块策略）
        
        将文档按段落切分，然后组合成大小合适的块。
        """
        paragraphs = self._split_into_paragraphs(content)
        chunks = []
        current_chunk_parts = []
        current_chunk_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # 如果当前段落本身就超过了最大块大小，需要切分
            if para_size > self.max_chunk_size:
                # 先刷新当前块
                if current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunk = DocumentChunk(
                        content=chunk_text,
                        document_id=document_id,
                        document_title=document_title,
                        chunk_type="text",
                        metadata=metadata or {}
                    )
                    chunks.append(chunk)
                    current_chunk_parts = []
                    current_chunk_size = 0
                
                # 切分大段落
                sub_chunks = self._split_text_into_chunks(
                    para,
                    max_size=self.max_chunk_size,
                    overlap=int(self.max_chunk_size * self.chunk_overlap)
                )
                for sub_content in sub_chunks:
                    chunk = DocumentChunk(
                        content=sub_content,
                        document_id=document_id,
                        document_title=document_title,
                        chunk_type="text",
                        metadata=metadata or {}
                    )
                    chunks.append(chunk)
            
            # 判断加入后是否超过最大块大小
            elif current_chunk_size + para_size > self.max_chunk_size and current_chunk_parts:
                # 当前块已满，保存并新建
                chunk_text = "\n\n".join(current_chunk_parts)
                chunk = DocumentChunk(
                    content=chunk_text,
                    document_id=document_id,
                    document_title=document_title,
                    chunk_type="text",
                    metadata=metadata or {}
                )
                chunks.append(chunk)
                current_chunk_parts = [para]
                current_chunk_size = para_size
            else:
                current_chunk_parts.append(para)
                current_chunk_size += para_size

        # 处理最后一个块
        if current_chunk_parts:
            chunk_text = "\n\n".join(current_chunk_parts)
            chunk = DocumentChunk(
                content=chunk_text,
                document_id=document_id,
                document_title=document_title,
                chunk_type="text",
                metadata=metadata or {}
            )
            chunks.append(chunk)

        return chunks

    # ============== 辅助方法 ==============

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """将文本按段落分割"""
        # 按空行分割段落
        paragraphs = re.split(r'\n\s*\n', content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_text_into_chunks(
        self,
        text: str,
        max_size: int,
        overlap: int = 0
    ) -> List[str]:
        """
        将长文本切分为多个块
        
        Args:
            text: 文本内容
            max_size: 最大块大小
            overlap: 块之间的重叠字符数
            
        Returns:
            切分后的文本块列表
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + max_size, len(text))
            
            # 尝试在句子结束处切分
            if end < len(text):
                # 向后查找最近的句号、问号、感叹号
                search_end = min(end + 100, len(text))
                sentence_end = text.rfind('。', start, search_end)
                if sentence_end == -1:
                    sentence_end = text.rfind('！', start, search_end)
                if sentence_end == -1:
                    sentence_end = text.rfind('？', start, search_end)
                if sentence_end == -1:
                    sentence_end = text.rfind('. ', start, search_end)
                
                if sentence_end > start + max_size // 2:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 移动起始位置，考虑重叠
            if end >= len(text):
                break
            start = end - overlap
            if start >= len(text):
                break

        return chunks

    def _detect_heading(self, text: str) -> bool:
        """
        检测一段文本是否为标题
        
        判断规则：
        1. 以数字编号开头（如 "1. ", "1.1 ", "第一章"）
        2. 长度较短（< 80 字）
        3. 不以句号、问号等结尾
        """
        text = text.strip()
        
        # 长度判断
        if len(text) > 80 or len(text) < 2:
            return False
        
        # 不以标点符号结尾
        if text[-1] in '。！？.!?；;，,':
            return False
        
        # 以数字编号开头
        if re.match(r'^\d+(\.\d+)*[\.、\s]', text):
            return True
        
        # 以"第X章/节/条/部分"开头
        if re.match(r'^第[一二三四五六七八九十百千\d]+[章节条部分篇]', text):
            return True
        
        # 全是大写字母（英文标题）
        if re.match(r'^[A-Z\s]+$', text) and len(text) > 3:
            return True
        
        return False

    def _normalize_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        规范化块列表
        
        - 合并过小的块（与前一个块合并）
        - 确保每个块都有内容
        """
        if not chunks:
            return chunks
        
        normalized = []
        
        for chunk in chunks:
            if not chunk.content or not chunk.content.strip():
                continue
            
            # 如果当前块太小，且上一个块也不大，则合并
            if (normalized 
                and len(chunk.content) < self.min_chunk_size
                and len(normalized[-1].content) + len(chunk.content) < self.max_chunk_size):
                # 合并到上一个块
                prev = normalized[-1]
                prev.content = prev.content + "\n\n" + chunk.content
                # 保留上一个块的结构信息
            else:
                normalized.append(chunk)
        
        return normalized


# 全局单例
_default_chunker: Optional[DocumentChunker] = None


def get_default_chunker() -> DocumentChunker:
    """获取默认的文档分块器"""
    global _default_chunker
    if _default_chunker is None:
        _default_chunker = DocumentChunker()
    return _default_chunker


__all__ = [
    "DocumentChunk",
    "DocumentChunker",
    "get_default_chunker",
]
