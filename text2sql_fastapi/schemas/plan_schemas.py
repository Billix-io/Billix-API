"""
Pydantic schemas for subscription plans, including creation and output formats.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from typing import Optional, List, Dict

class PlanBase(BaseModel):
    """
    Base schema for subscription plan information, including pricing and features.
    """
    title: str
    description: Optional[str] = None
    monthlyPrice: float
    yearlyPrice: float
    priceId: Optional[str] = None
    features: List[Dict[str, str]]
    tokens: int

class PlanCreate(PlanBase):
    """
    Schema for creating a new subscription plan.
    """
    pass

class PlanOut(PlanBase):
    """
    Schema for outputting subscription plan details, including plan ID.
    """
    plan_id: UUID 

    class Config:
        orm_mode = True 