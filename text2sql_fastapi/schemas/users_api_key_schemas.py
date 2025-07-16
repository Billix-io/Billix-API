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
    user_id: str
    name: str
    is_active: bool = True
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
    user_id: str
    users_api_key_id: UUID
    api_key: str
    is_active: bool = True
    created_at: datetime

    class Config:
        orm_mode = True

class UsersApiKeyUpdate(BaseModel):
    """
    Schema for updating API key status (enable/disable).
    """
    is_active: bool

class UsersApiKeyToggle(BaseModel):
    """
    Schema for toggling API key status.
    """
    is_active: bool 