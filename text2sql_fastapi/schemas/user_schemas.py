"""
Pydantic schemas for user data, authentication, creation, update, and response formats.
"""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Optional
from .roles_schemas import RoleResponse


class UserBase(BaseModel):
    """
    Base schema for user information, including email, name, and phone number.
    """
    email: EmailStr
    first_name: str
    last_name: str
    
    phone_number: Optional[str] = None
    

class UserLogin(BaseModel):
    """
    Schema for user login credentials.
    """
    email: str
    password: str
    remember_me: bool = False

class UserUpdate(BaseModel):
    """
    Schema for updating user fields.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    google_id: Optional[str] = None
    otp_code: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    password_hash: Optional[str] = None
    role_id: Optional[str] = None
    status_active: Optional[bool] = None


class UserResponse(UserBase):
    """
    Schema for user response, including IDs, timestamps, role, and status.
    """
    user_id: UUID
    created_at: datetime
    updated_at: datetime
  
    role: Optional[RoleResponse] = None
    status_active: bool
    is_verified: bool = False

    model_config = {
        "from_attributes": True
    }

class UserCreate(UserBase):
    """
    Schema for creating a new user, including password and optional Google ID.
    """
    password: str

class GoogleAuthModel(BaseModel):
    """
    Schema for Google authentication model, containing the ID token.
    """
    id_token: str
   