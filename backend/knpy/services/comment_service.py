from datetime import datetime
from typing import List, Optional

from knpy.core.database import SessionLocal
from knpy.core.exceptions import NotFoundError, PermissionError
from knpy.models.comment import Comment
from knpy.models.document import Document
from knpy.models.user import User
from knpy.schemas.comment import CommentCreate, CommentUpdate, CommentResponse


def get_comment(db, comment_id: int) -> Optional[Comment]:
    return db.query(Comment).filter(Comment.id == comment_id).first()


def get_comments(db, document_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
    return db.query(Comment).filter(Comment.document_id == document_id).offset(skip).limit(limit).all()


def create_comment(db, comment_create: CommentCreate, user_id: int) -> Comment:
    document = db.query(Document).filter(Document.id == comment_create.document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    comment = Comment(
        document_id=comment_create.document_id,
        content=comment_create.content,
        parent_id=comment_create.parent_id,
        author_id=user_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db, comment_id: int, comment_update: CommentUpdate, user_id: int) -> Comment:
    comment = get_comment(db, comment_id)
    if not comment:
        raise NotFoundError("Comment not found")
    
    if comment.author_id != user_id:
        raise PermissionError("You are not the owner of this comment")
    
    if comment_update.content:
        comment.content = comment_update.content
    
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db, comment_id: int, user_id: int) -> None:
    comment = get_comment(db, comment_id)
    if not comment:
        raise NotFoundError("Comment not found")
    
    if comment.author_id != user_id:
        raise PermissionError("You are not the owner of this comment")
    
    db.delete(comment)
    db.commit()


def get_comment_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        document_id=comment.document_id,
        content=comment.content,
        parent_id=comment.parent_id,
        author_id=comment.author_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )
