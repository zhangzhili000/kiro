from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from ...models import Comment

router = APIRouter(prefix="/comments", tags=["评论"])


@router.get("/documents/{document_id}", response_model=List[CommentResponse])
def list_comments(document_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(
        Comment.document_id == document_id,
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).all()
    return comments


@router.post("/documents/{document_id}", response_model=CommentResponse)
def create_comment(document_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    db_comment = Comment(**comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(comment_id: int, comment_update: CommentUpdate, db: Session = Depends(get_db)):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    db_comment.content = comment_update.content
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    db_comment.is_deleted = True
    db.commit()
    return {"message": "删除成功"}


@router.post("/{comment_id}/reply", response_model=CommentResponse)
def reply_comment(comment_id: int, reply: CommentCreate, db: Session = Depends(get_db)):
    parent_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not parent_comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    db_reply = Comment(
        document_id=reply.document_id,
        user_id=reply.user_id,
        parent_id=comment_id,
        content=reply.content
    )
    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)
    return db_reply
