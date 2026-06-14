from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...schemas.notification import NotificationResponse, NotificationUpdate
from ...models import Notification

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=List[NotificationResponse])
def list_notifications(db: Session = Depends(get_db)):
    notifications = db.query(Notification).order_by(Notification.created_at.desc()).all()
    return notifications


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.put("/read-all")
def mark_all_as_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "全部已读"}
