from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from models.enums import RoleEnum

class RoleBase(BaseModel):
    name: RoleEnum
    description: Optional[str] = None

 

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[RoleEnum] = None
    description: Optional[str] = None
    status_active: Optional[bool] = None

class RoleResponse(RoleBase):
    role_id: UUID
    status_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }