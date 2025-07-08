"""
Pydantic schemas for user usage records, including creation, update, and response formats.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserUsageBase(BaseModel):
    userId: str
    chatUsage: int
    invoiceUsage: int
    resetDate: datetime
    createdAt: datetime
    updatedAt: datetime

class UserUsageCreate(BaseModel):
    userId: str

class UserUsageUpdate(BaseModel):
    chatUsage: Optional[int] = None
    invoiceUsage: Optional[int] = None
    resetDate: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class UserUsageInDB(UserUsageBase):
    id: str
    class Config:
        from_attributes = True

class UserUsageResponse(UserUsageInDB):
    pass 