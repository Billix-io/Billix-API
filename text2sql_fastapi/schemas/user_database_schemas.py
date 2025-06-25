from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime

class UserDatabaseBase(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password_encrypted: str
    database_name: str
    connection_status: str = "pending"
    last_synced_at: Optional[datetime] = None

class UserDatabaseCreate(UserDatabaseBase):
    user_id: UUID4

class UserDatabaseUpdate(BaseModel):
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password_encrypted: Optional[str] = None
    database_name: Optional[str] = None
    connection_status: Optional[str] = None
    last_synced_at: Optional[datetime] = None

class UserDatabaseInDB(UserDatabaseBase):
    db_id: UUID4
    user_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class UserDatabaseResponse(UserDatabaseInDB):
    pass 