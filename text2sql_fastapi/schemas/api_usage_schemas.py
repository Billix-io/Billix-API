"""
Pydantic schemas for API usage records, including creation, update, and response formats.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ApiUsageBase(BaseModel):
    """
    Base schema for API usage information, matching the ApiUsage model fields.
    """
    userId: str

class ApiUsageCreate(ApiUsageBase):
    """
    Schema for creating a new API usage record. chatUsage and invoiceUsage are not included and default to 0 in the model.
    """
    pass

class ApiUsageUpdate(BaseModel):
    """
    Schema for updating API usage fields.
    """
    chatUsage: Optional[int] = None
    invoiceUsage: Optional[int] = None
    resetDate: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class ApiUsageInDB(ApiUsageBase):
    """
    Schema for API usage data as stored in the database, including the record ID.
    """
    id: uuid.UUID
    chatUsage: int
    invoiceUsage: int
    resetDate: datetime
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class ApiUsageResponse(ApiUsageInDB):
    """
    Schema for API usage response, inherits from ApiUsageInDB.
    """
    pass 