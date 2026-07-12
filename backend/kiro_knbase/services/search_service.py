from datetime import datetime
from typing import List, Optional

from kiro_platform.core.database import SessionLocal
from kiro_platform.core.exceptions import NotFoundError
from kiro_knbase.models.document import Document
from kiro_platform.models.notification import SearchHistory
from kiro_knbase.schemas.document import DocumentResponse


def search_documents(db, query: str, category_id: Optional[int] = None, sort_by: str = 'relevance', skip: int = 0, limit: int = 100) -> List[Document]:
    q = db.query(Document).filter(Document.deleted_at.is_(None))
    
    if query:
        q = q.filter(
            (Document.title.ilike(f'%{query}%')) |
            (Document.content.ilike(f'%{query}%'))
        )
    
    if category_id:
        q = q.filter(Document.category_id == category_id)
    
    if sort_by == 'time':
        q = q.order_by(Document.updated_at.desc())
    elif sort_by == 'hot':
        q = q.order_by(Document.view_count.desc())
    else:
        q = q.order_by(Document.created_at.desc())
    
    return q.offset(skip).limit(limit).all()


def record_search_history(db, user_id: int, query: str) -> SearchHistory:
    history = SearchHistory(
        user_id=user_id,
        query=query
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_search_history(db, user_id: int, skip: int = 0, limit: int = 100) -> List[SearchHistory]:
    return db.query(SearchHistory).filter(SearchHistory.user_id == user_id).offset(skip).limit(limit).all()


def clear_search_history(db, user_id: int) -> None:
    db.query(SearchHistory).filter(SearchHistory.user_id == user_id).delete()
    db.commit()


def increment_view_count(db, document_id: int) -> None:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        document.view_count += 1
        db.commit()
