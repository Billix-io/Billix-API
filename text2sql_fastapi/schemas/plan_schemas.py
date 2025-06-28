from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tokens: int

class PlanCreate(PlanBase):
    pass

class PlanOut(PlanBase):
    plan_id: UUID

    class Config:
        orm_mode = True 