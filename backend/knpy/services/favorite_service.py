from typing import List, Optional

from kiro.core.database import SessionLocal
from kiro.core.exceptions import NotFoundError
from kiro.models.user_favorite import UserFavorite, DocumentLike
from kiro.models.document import Document
from kiro.models.user import User
from kiro.schemas.favorite import FavoriteCreate, FavoriteResponse
from kiro.schemas.like import LikeCreate, LikeResponse


def get_favorite(db, user_id: int, document_id: int) -> Optional[UserFavorite]:
    return db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.document_id == document_id
    ).first()


def get_favorites_by_user(db, user_id: int, skip: int = 0, limit: int = 100) -> List[UserFavorite]:
    return db.query(UserFavorite).filter(UserFavorite.user_id == user_id).offset(skip).limit(limit).all()


def create_favorite(db, favorite_create: FavoriteCreate, user_id: int) -> UserFavorite:
    existing = get_favorite(db, user_id, favorite_create.document_id)
    if existing:
        return existing
    
    document = db.query(Document).filter(Document.id == favorite_create.document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    favorite = UserFavorite(
        user_id=user_id,
        document_id=favorite_create.document_id
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def delete_favorite(db, user_id: int, document_id: int) -> None:
    favorite = get_favorite(db, user_id, document_id)
    if not favorite:
        raise NotFoundError("Favorite not found")
    
    db.delete(favorite)
    db.commit()


def get_like(db, user_id: int, document_id: int) -> Optional[DocumentLike]:
    return db.query(DocumentLike).filter(
        DocumentLike.user_id == user_id,
        DocumentLike.document_id == document_id
    ).first()


def create_like(db, like_create: LikeCreate, user_id: int) -> DocumentLike:
    existing = get_like(db, user_id, like_create.document_id)
    if existing:
        return existing
    
    document = db.query(Document).filter(Document.id == like_create.document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    like = DocumentLike(
        user_id=user_id,
        document_id=like_create.document_id
    )
    db.add(like)
    db.commit()
    db.refresh(like)
    
    document.like_count += 1
    db.commit()
    
    return like


def delete_like(db, user_id: int, document_id: int) -> None:
    like = get_like(db, user_id, document_id)
    if not like:
        raise NotFoundError("Like not found")
    
    db.delete(like)
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if document and document.like_count > 0:
        document.like_count -= 1
    
    db.commit()


def get_favorite_response(favorite: UserFavorite) -> FavoriteResponse:
    return FavoriteResponse(
        id=favorite.id,
        user_id=favorite.user_id,
        document_id=favorite.document_id,
        created_at=favorite.created_at
    )


def get_like_response(like: DocumentLike) -> LikeResponse:
    return LikeResponse(
        id=like.id,
        user_id=like.user_id,
        document_id=like.document_id,
        created_at=like.created_at
    )
