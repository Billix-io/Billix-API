from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Optional
from .roles_schemas import RoleResponse


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    
    phone_number: Optional[str] = None
    

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class UserUpdate(BaseModel):
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
    password: str
    google_id: Optional[str] = None

class GoogleAuthModel(BaseModel):
    id_token: str
   