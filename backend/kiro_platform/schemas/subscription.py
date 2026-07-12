from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionBase(BaseModel):
    subscription_type: str
    target_id: int


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    subscription_type: str
    target_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
