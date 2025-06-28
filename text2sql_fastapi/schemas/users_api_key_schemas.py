from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class UsersApiKeyBase(BaseModel):
    user_id: UUID
    expires_at: Optional[datetime] = None

class UsersApiKeyCreate(UsersApiKeyBase):
    pass

class UsersApiKeyOut(UsersApiKeyBase):
    user_id: UUID
    users_api_key_id: UUID
    api_key: str
    created_at: datetime

    class Config:
        orm_mode = True 