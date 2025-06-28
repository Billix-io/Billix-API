from pydantic import BaseModel, UUID4, condecimal
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class UserSubscriptionBase(BaseModel):
    user_id: UUID   
    plan_id: UUID
    

class UserSubscriptionCreate(UserSubscriptionBase):
    pass

class UserSubscriptionUpdate(BaseModel):
    tokens_remaining: Optional[int] = None
    plan_id: Optional[int] = None
   

class UserSubscriptionInDB(UserSubscriptionBase):
    subscription_id: UUID4
    total_tokens_purchased: int
    tokens_remaining: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserSubscriptionResponse(UserSubscriptionInDB):
    pass 