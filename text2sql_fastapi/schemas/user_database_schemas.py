from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime

"""
Pydantic schemas for user database connections, including creation, update, and response formats.
"""

class UserDatabaseBase(BaseModel):
    """
    Base schema for user database connection information.
    """
    db_type: str
    host: str
    port: int
    username: str
    password_encrypted: str
    database_name: str
    connection_status: str = "pending"
    last_synced_at: Optional[datetime] = None

class UserDatabaseCreate(UserDatabaseBase):
    """
    Schema for creating a new user database connection.
    """
    user_id: UUID4

class UserDatabaseUpdate(BaseModel):
    """
    Schema for updating user database connection fields.
    """
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password_encrypted: Optional[str] = None
    database_name: Optional[str] = None
    connection_status: Optional[str] = None
    last_synced_at: Optional[datetime] = None

class UserDatabaseInDB(UserDatabaseBase):
    """
    Schema for user database data as stored in the database, including IDs and timestamps.
    """
    db_id: UUID4
    user_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class UserDatabaseResponse(UserDatabaseInDB):
    """
    Schema for user database response, inherits from UserDatabaseInDB.
    """
    pass 