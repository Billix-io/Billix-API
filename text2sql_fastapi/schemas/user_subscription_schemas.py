"""
Pydantic schemas for user subscriptions, including creation, update, and response formats.
"""
from pydantic import BaseModel, UUID4, condecimal
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class UserSubscriptionBase(BaseModel):
    """
    Base schema for user subscription information, including user and plan IDs.
    """
    user_id: UUID   
    plan_id: UUID
    

class UserSubscriptionCreate(UserSubscriptionBase):
    """
    Schema for creating a new user subscription.
    """
    pass

class UserSubscriptionUpdate(BaseModel):
    """
    Schema for updating user subscription fields.
    """
    tokens_remaining: Optional[int] = None
    plan_id: Optional[int] = None
   

class UserSubscriptionInDB(UserSubscriptionBase):
    """
    Schema for user subscription data as stored in the database, including IDs and timestamps.
    """
    subscription_id: UUID4
    total_tokens_purchased: int
    tokens_remaining: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserSubscriptionResponse(UserSubscriptionInDB):
    """
    Schema for user subscription response, inherits from UserSubscriptionInDB.
    """
    pass 