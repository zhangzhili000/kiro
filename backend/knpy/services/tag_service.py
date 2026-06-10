from typing import List, Optional

from kiro.core.database import SessionLocal
from kiro.core.exceptions import NotFoundError
from kiro.models.category import Tag, DocumentTag
from kiro.schemas.tag import TagCreate, TagUpdate, TagResponse


def get_tag(db, tag_id: int) -> Optional[Tag]:
    return db.query(Tag).filter(Tag.id == tag_id).first()


def get_tags(db, skip: int = 0, limit: int = 100) -> List[Tag]:
    return db.query(Tag).offset(skip).limit(limit).all()


def create_tag(db, tag_create: TagCreate) -> Tag:
    tag = Tag(
        name=tag_create.name,
        color=tag_create.color or '#409eff'
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def update_tag(db, tag_id: int, tag_update: TagUpdate) -> Tag:
    tag = get_tag(db, tag_id)
    if not tag:
        raise NotFoundError("Tag not found")
    
    if tag_update.name:
        tag.name = tag_update.name
    if tag_update.color:
        tag.color = tag_update.color
    
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db, tag_id: int) -> None:
    tag = get_tag(db, tag_id)
    if not tag:
        raise NotFoundError("Tag not found")
    
    db.query(DocumentTag).filter(DocumentTag.tag_id == tag_id).delete()
    db.delete(tag)
    db.commit()


def get_tags_by_document(db, document_id: int) -> List[Tag]:
    return db.query(Tag).join(DocumentTag).filter(DocumentTag.document_id == document_id).all()


def get_tag_response(tag: Tag) -> TagResponse:
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at,
        updated_at=tag.updated_at
    )
