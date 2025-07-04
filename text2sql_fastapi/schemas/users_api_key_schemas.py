"""
Pydantic schemas for user API keys, including creation and output formats.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class UsersApiKeyBase(BaseModel):
    """
    Base schema for user API key information, including user ID and expiration.
    """
    user_id: UUID
    expires_at: Optional[datetime] = None

class UsersApiKeyCreate(UsersApiKeyBase):
    """
    Schema for creating a new user API key.
    """
    pass

class UsersApiKeyOut(UsersApiKeyBase):
    """
    Schema for outputting user API key details, including IDs and timestamps.
    """
    user_id: UUID
    users_api_key_id: UUID
    api_key: str
    created_at: datetime

    class Config:
        orm_mode = True 