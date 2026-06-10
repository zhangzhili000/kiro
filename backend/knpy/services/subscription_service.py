from typing import List, Optional

from kiro.core.database import SessionLocal
from kiro.core.exceptions import NotFoundError
from kiro.models.user_favorite import Subscription
from kiro.models.user import User
from kiro.schemas.subscription import SubscriptionCreate, SubscriptionResponse


def get_subscription(db, user_id: int, target_user_id: int) -> Optional[Subscription]:
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.target_user_id == target_user_id
    ).first()


def get_subscriptions(db, user_id: int, skip: int = 0, limit: int = 100) -> List[Subscription]:
    return db.query(Subscription).filter(Subscription.user_id == user_id).offset(skip).limit(limit).all()


def get_subscribers(db, target_user_id: int, skip: int = 0, limit: int = 100) -> List[Subscription]:
    return db.query(Subscription).filter(Subscription.target_user_id == target_user_id).offset(skip).limit(limit).all()


def create_subscription(db, subscription_create: SubscriptionCreate, user_id: int) -> Subscription:
    existing = get_subscription(db, user_id, subscription_create.target_user_id)
    if existing:
        return existing
    
    target_user = db.query(User).filter(User.id == subscription_create.target_user_id).first()
    if not target_user:
        raise NotFoundError("Target user not found")
    
    subscription = Subscription(
        user_id=user_id,
        target_user_id=subscription_create.target_user_id
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(db, user_id: int, target_user_id: int) -> None:
    subscription = get_subscription(db, user_id, target_user_id)
    if not subscription:
        raise NotFoundError("Subscription not found")
    
    db.delete(subscription)
    db.commit()


def get_subscription_response(subscription: Subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        target_user_id=subscription.target_user_id,
        created_at=subscription.created_at
    )
