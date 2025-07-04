"""
Pydantic schemas for Help and Support tickets, including creation and response formats.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class HelpAndSupportBase(BaseModel):
    """
    Base schema for help and support ticket information.
    """
    name:str
    phone_number:str
    email:str
    message: str

class HelpAndSupportCreate(HelpAndSupportBase):
    """
    Schema for creating a new help and support ticket.
    """
    pass

class HelpAndSupportResponse(HelpAndSupportBase):
    """
    Schema for help and support ticket response, including status and timestamps.
    """
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
