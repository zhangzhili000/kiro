from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...api.v1.users import get_current_user
from ...models.user import User
from ...schemas.subscription import SubscriptionCreate, SubscriptionResponse
from ...models import Subscription, Document, Category, User as UserModel

router = APIRouter(prefix="/subscriptions", tags=["订阅"])


@router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的订阅列表"""
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True
    ).all()
    return subscriptions


@router.post("", response_model=SubscriptionResponse)
def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订阅（支持分类、作者、文档订阅）"""
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.subscription_type == subscription.subscription_type,
        Subscription.target_id == subscription.target_id
    ).first()

    if existing:
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    db_subscription = Subscription(
        **subscription.model_dump(exclude={"user_id"}),
        user_id=current_user.id
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


@router.delete("/{subscription_id}")
def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消订阅"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅不存在")

    subscription.is_active = False
    db.commit()
    return {"message": "取消订阅成功"}


@router.get("/feed")
def get_subscription_feed(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订阅推送内容（按订阅的分类、作者、文档更新）"""
    # 获取用户的订阅
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True
    ).all()

    # 获取订阅的目标ID
    category_ids = []
    author_ids = []
    document_ids = []

    for sub in subscriptions:
        if sub.subscription_type == "category":
            category_ids.append(sub.target_id)
        elif sub.subscription_type == "author":
            author_ids.append(sub.target_id)
        elif sub.subscription_type == "document":
            document_ids.append(sub.target_id)

    # 查询更新的内容
    query = db.query(Document).filter(Document.is_deleted == False)
    
    conditions = []
    if category_ids:
        conditions.append(Document.category_id.in_(category_ids))
    if author_ids:
        conditions.append(Document.author_id.in_(author_ids))
    if document_ids:
        conditions.append(Document.id.in_(document_ids))
    
    if conditions:
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
    
    query = query.order_by(Document.updated_at.desc())
    
    offset = (page - 1) * page_size
    documents = query.offset(offset).limit(page_size).all()
    total = query.count()

    results = []
    for doc in documents:
        results.append({
            "id": doc.id,
            "title": doc.title,
            "author_id": doc.author_id,
            "category_id": doc.category_id,
            "updated_at": doc.updated_at
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results
    }


@router.post("/category/{category_id}")
def subscribe_to_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订阅分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.subscription_type == "category",
        Subscription.target_id == category_id
    ).first()

    if existing:
        existing.is_active = True
        db.commit()
        return {"message": "已订阅该分类"}

    subscription = Subscription(
        user_id=current_user.id,
        subscription_type="category",
        target_id=category_id
    )
    db.add(subscription)
    db.commit()
    return {"message": "订阅成功"}


@router.post("/author/{user_id}")
def subscribe_to_author(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订阅作者"""
    author = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.subscription_type == "author",
        Subscription.target_id == user_id
    ).first()

    if existing:
        existing.is_active = True
        db.commit()
        return {"message": "已订阅该作者"}

    subscription = Subscription(
        user_id=current_user.id,
        subscription_type="author",
        target_id=user_id
    )
    db.add(subscription)
    db.commit()
    return {"message": "订阅成功"}


@router.post("/document/{document_id}")
def subscribe_to_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订阅文档"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.subscription_type == "document",
        Subscription.target_id == document_id
    ).first()

    if existing:
        existing.is_active = True
        db.commit()
        return {"message": "已订阅该文档"}

    subscription = Subscription(
        user_id=current_user.id,
        subscription_type="document",
        target_id=document_id
    )
    db.add(subscription)
    db.commit()
    return {"message": "订阅成功"}
