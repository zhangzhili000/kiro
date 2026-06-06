from datetime import datetime, timedelta
from knpy.core.timezone_utils import get_beijing_time
from typing import List, Optional

from knpy.core.database import SessionLocal
from knpy.core.exceptions import NotFoundError, PermissionError
from knpy.models.document import Document
from knpy.models.document_version import DocumentVersion, DocumentShare
from knpy.models.category import Category
from knpy.models.category import DocumentTag
from knpy.models.user import User
from knpy.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse


def get_document(db, document_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents(db, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[Document]:
    query = db.query(Document).filter(Document.deleted_at.is_(None))
    if category_id:
        query = query.filter(Document.category_id == category_id)
    return query.offset(skip).limit(limit).all()


def create_document(db, document_create: DocumentCreate, user_id: int) -> Document:
    document = Document(
        title=document_create.title,
        content=document_create.content,
        category_id=document_create.category_id,
        permission=document_create.permission or 'public',
        author_id=user_id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    create_document_version(db, document.id, document.content, user_id)
    
    if document_create.tag_ids:
        for tag_id in document_create.tag_ids:
            doc_tag = DocumentTag(document_id=document.id, tag_id=tag_id)
            db.add(doc_tag)
        db.commit()
    
    return document


def update_document(db, document_id: int, document_update: DocumentUpdate, user_id: int) -> Document:
    document = get_document(db, document_id)
    if not document:
        raise NotFoundError("Document not found")
    
    if document.author_id != user_id:
        raise PermissionError("You are not the owner of this document")
    
    if document_update.title:
        document.title = document_update.title
    if document_update.content:
        document.content = document_update.content
        create_document_version(db, document.id, document.content, user_id)
    if document_update.category_id:
        document.category_id = document_update.category_id
    if document_update.permission:
        document.permission = document_update.permission
    
    if document_update.tag_ids is not None:
        db.query(DocumentTag).filter(DocumentTag.document_id == document.id).delete()
        for tag_id in document_update.tag_ids:
            doc_tag = DocumentTag(document_id=document.id, tag_id=tag_id)
            db.add(doc_tag)
    
    db.commit()
    db.refresh(document)
    return document


def delete_document(db, document_id: int, user_id: int) -> None:
    document = get_document(db, document_id)
    if not document:
        raise NotFoundError("Document not found")
    
    if document.author_id != user_id:
        raise PermissionError("You are not the owner of this document")
    
    document.deleted_at = get_beijing_time()
    db.commit()


def restore_document(db, document_id: int) -> Document:
    document = db.query(Document).filter(Document.id == document_id, Document.deleted_at.isnot(None)).first()
    if not document:
        raise NotFoundError("Document not found in trash")
    
    document.deleted_at = None
    db.commit()
    db.refresh(document)
    return document


def create_document_version(db, document_id: int, content: str, user_id: int) -> DocumentVersion:
    version = DocumentVersion(
        document_id=document_id,
        content=content,
        created_by=user_id
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def get_document_versions(db, document_id: int) -> List[DocumentVersion]:
    return db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).order_by(DocumentVersion.created_at.desc()).all()


def get_document_response(document: Document, user: Optional[User] = None) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        category_id=document.category_id,
        permission=document.permission,
        author_id=document.author_id,
        view_count=document.view_count,
        like_count=document.like_count,
        created_at=document.created_at,
        updated_at=document.updated_at
    )
