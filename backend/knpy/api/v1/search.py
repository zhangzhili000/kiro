from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...core.database import get_db
from ...schemas.document import DocumentListResponse
from ...schemas.common import PageParams
from ...models import Document, SearchHistory, DocumentTag

router = APIRouter(prefix="/search", tags=["搜索"])


def highlight_keyword(content: str, keyword: str) -> str:
    """在内容中高亮显示关键词"""
    if not content or not keyword:
        return content
    return content.replace(keyword, f"<mark>{keyword}</mark>")


@router.get("", response_model=List[Dict[str, Any]])
def search_documents(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    sort_by: Optional[str] = "relevance",
    page: int = 1,
    page_size: int = 20,
    highlight: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(
        Document.is_deleted == False,
        or_(
            Document.title.ilike(f"%{q}%"),
            Document.content.ilike(f"%{q}%")
        )
    )

    if category_id:
        query = query.filter(Document.category_id == category_id)

    if tag_id:
        query = query.join(DocumentTag, Document.id == DocumentTag.document_id)\
                    .filter(DocumentTag.tag_id == tag_id)

    if sort_by == "time":
        query = query.order_by(Document.updated_at.desc())
    elif sort_by == "hot":
        query = query.order_by(Document.view_count.desc())
    elif sort_by == "relevance":
        # 简单的相关性排序：标题匹配优先
        title_match = func.lower(Document.title).like(f"%{q.lower()}%")
        content_match = func.lower(Document.content).like(f"%{q.lower()}%")
        query = query.order_by(
            title_match.desc(),
            content_match.desc(),
            Document.updated_at.desc()
        )
    else:
        query = query.order_by(Document.updated_at.desc())

    offset = (page - 1) * page_size
    documents = query.offset(offset).limit(page_size).all()

    search_history = SearchHistory(
        user_id=1,
        keyword=q,
        result_count=len(documents)
    )
    db.add(search_history)
    db.commit()

    results = []
    for doc in documents:
        doc_dict = {
            "id": doc.id,
            "title": highlight_keyword(doc.title, q) if highlight else doc.title,
            "content": highlight_keyword(doc.content[:200] + "..." if len(doc.content) > 200 else doc.content, q) if highlight else doc.content,
            "category_id": doc.category_id,
            "author_id": doc.author_id,
            "permission": doc.permission,
            "view_count": doc.view_count,
            "like_count": doc.like_count,
            "comment_count": doc.comment_count,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        }
        results.append(doc_dict)

    return results


@router.get("/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    suggestions = db.query(Document.title).filter(
        Document.title.ilike(f"%{q}%"),
        Document.is_deleted == False
    ).limit(10).all()

    return [s[0] for s in suggestions]


@router.post("/advanced")
def advanced_search(
    keywords: Optional[str] = None,
    title_only: bool = False,
    content_only: bool = False,
    category_ids: Optional[List[int]] = Body(None),
    tag_ids: Optional[List[int]] = Body(None),
    author_ids: Optional[List[int]] = Body(None),
    permission: Optional[str] = None,
    status: Optional[str] = None,
    min_view_count: Optional[int] = None,
    max_view_count: Optional[int] = None,
    min_like_count: Optional[int] = None,
    max_like_count: Optional[int] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    updated_after: Optional[str] = None,
    updated_before: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """高级搜索 - 支持多条件组合搜索"""
    query = db.query(Document).filter(Document.is_deleted == False)

    # 关键词搜索
    if keywords:
        if title_only:
            query = query.filter(Document.title.ilike(f"%{keywords}%"))
        elif content_only:
            query = query.filter(Document.content.ilike(f"%{keywords}%"))
        else:
            query = query.filter(
                or_(
                    Document.title.ilike(f"%{keywords}%"),
                    Document.content.ilike(f"%{keywords}%")
                )
            )

    # 分类筛选
    if category_ids and len(category_ids) > 0:
        query = query.filter(Document.category_id.in_(category_ids))

    # 标签筛选
    if tag_ids and len(tag_ids) > 0:
        query = query.join(DocumentTag, Document.id == DocumentTag.document_id)\
                    .filter(DocumentTag.tag_id.in_(tag_ids))

    # 作者筛选
    if author_ids and len(author_ids) > 0:
        query = query.filter(Document.author_id.in_(author_ids))

    # 权限筛选
    if permission:
        query = query.filter(Document.permission == permission)

    # 状态筛选
    if status:
        query = query.filter(Document.status == status)

    # 浏览量范围
    if min_view_count is not None:
        query = query.filter(Document.view_count >= min_view_count)
    if max_view_count is not None:
        query = query.filter(Document.view_count <= max_view_count)

    # 点赞数范围
    if min_like_count is not None:
        query = query.filter(Document.like_count >= min_like_count)
    if max_like_count is not None:
        query = query.filter(Document.like_count <= max_like_count)

    # 创建时间范围
    try:
        if created_after:
            query = query.filter(Document.created_at >= datetime.fromisoformat(created_after))
        if created_before:
            query = query.filter(Document.created_at <= datetime.fromisoformat(created_before))
    except ValueError:
        pass

    # 更新时间范围
    try:
        if updated_after:
            query = query.filter(Document.updated_at >= datetime.fromisoformat(updated_after))
        if updated_before:
            query = query.filter(Document.updated_at <= datetime.fromisoformat(updated_before))
    except ValueError:
        pass

    # 排序
    sort_column = getattr(Document, sort_by, Document.updated_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 分页
    offset = (page - 1) * page_size
    documents = query.offset(offset).limit(page_size).all()
    total = query.count()

    results = []
    for doc in documents:
        doc_dict = {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content[:200] + "..." if len(doc.content or "") > 200 else doc.content,
            "category_id": doc.category_id,
            "author_id": doc.author_id,
            "permission": doc.permission,
            "status": doc.status,
            "view_count": doc.view_count,
            "like_count": doc.like_count,
            "comment_count": doc.comment_count,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        }
        results.append(doc_dict)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results
    }


@router.get("/similar/{document_id}")
def get_similar_documents(
    document_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取相似文档推荐"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="文档不存在")

    # 获取文档的标签
    doc_tags = db.query(DocumentTag.tag_id).filter(DocumentTag.document_id == document_id).all()
    doc_tag_ids = [tag[0] for tag in doc_tags]

    # 构建相似文档查询
    # 优先级：相同分类 > 相同标签 > 标题/内容关键词匹配
    query = db.query(Document).filter(
        Document.id != document_id,
        Document.is_deleted == False
    )

    # 获取相似文档（基于分类和标签）
    similar_docs = []
    
    # 1. 相同分类的文档
    if document.category_id:
        category_docs = db.query(Document).filter(
            Document.id != document_id,
            Document.category_id == document.category_id,
            Document.is_deleted == False
        ).limit(limit).all()
        similar_docs.extend(category_docs)

    # 2. 相同标签的文档
    if doc_tag_ids:
        tag_docs = db.query(Document).filter(
            Document.id != document_id,
            Document.is_deleted == False
        ).join(DocumentTag, Document.id == DocumentTag.document_id)\
         .filter(DocumentTag.tag_id.in_(doc_tag_ids))\
         .limit(limit).all()
        # 去重
        existing_ids = {doc.id for doc in similar_docs}
        similar_docs.extend([doc for doc in tag_docs if doc.id not in existing_ids])

    # 3. 基于关键词的相似性
    if document.title:
        keywords = [word for word in document.title.split() if len(word) > 2]
        if keywords:
            keyword_conditions = or_(*[Document.title.ilike(f"%{kw}%") for kw in keywords])
            keyword_docs = db.query(Document).filter(
                Document.id != document_id,
                Document.is_deleted == False,
                keyword_conditions
            ).limit(limit).all()
            existing_ids = {doc.id for doc in similar_docs}
            similar_docs.extend([doc for doc in keyword_docs if doc.id not in existing_ids])

    # 限制数量并去重
    seen_ids = set()
    final_results = []
    for doc in similar_docs:
        if doc.id not in seen_ids:
            seen_ids.add(doc.id)
            final_results.append(doc)
            if len(final_results) >= limit:
                break

    results = []
    for doc in final_results:
        results.append({
            "id": doc.id,
            "title": doc.title,
            "category_id": doc.category_id,
            "author_id": doc.author_id,
            "view_count": doc.view_count,
            "like_count": doc.like_count,
            "updated_at": doc.updated_at
        })

    return results
