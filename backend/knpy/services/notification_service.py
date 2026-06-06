from datetime import datetime
from typing import List, Optional

from knpy.core.database import SessionLocal
from knpy.core.exceptions import NotFoundError
from knpy.models.notification import Notification
from knpy.models.user import User
from knpy.schemas.notification import NotificationCreate, NotificationResponse


def get_notification(db, notification_id: int) -> Optional[Notification]:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def get_notifications(db, user_id: int, skip: int = 0, limit: int = 100) -> List[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).offset(skip).limit(limit).all()


def create_notification(db, notification_create: NotificationCreate) -> Notification:
    notification = Notification(
        user_id=notification_create.user_id,
        title=notification_create.title,
        content=notification_create.content,
        type=notification_create.type,
        related_id=notification_create.related_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_as_read(db, notification_id: int, user_id: int) -> Notification:
    notification = get_notification(db, notification_id)
    if not notification:
        raise NotFoundError("Notification not found")
    
    if notification.user_id != user_id:
        raise PermissionError("You can only mark your own notifications as read")
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db, user_id: int) -> None:
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update(
        {Notification.is_read: True}
    )
    db.commit()


def get_notification_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        title=notification.title,
        content=notification.content,
        type=notification.type,
        related_id=notification.related_id,
        is_read=notification.is_read,
        created_at=notification.created_at
    )


def get_unread_count(db, user_id: int) -> int:
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()
