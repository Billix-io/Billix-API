"""
Pydantic schemas for user roles, including creation, update, and response formats.
"""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from models.enums import RoleEnum

class RoleBase(BaseModel):
    """
    Base schema for user role information, including name and description.
    """
    name: RoleEnum
    description: Optional[str] = None

 

class RoleCreate(RoleBase):
    """
    Schema for creating a new user role.
    """
    pass

class RoleUpdate(BaseModel):
    """
    Schema for updating user role fields.
    """
    name: Optional[RoleEnum] = None
    description: Optional[str] = None
    status_active: Optional[bool] = None

class RoleResponse(RoleBase):
    """
    Schema for user role response, including IDs and timestamps.
    """
    role_id: UUID
    status_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }