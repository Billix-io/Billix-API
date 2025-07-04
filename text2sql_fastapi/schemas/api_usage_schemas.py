"""
Pydantic schemas for API usage records, including creation, update, and response formats.
"""
from pydantic import BaseModel, UUID4, condecimal, conint
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal

class ApiUsageBase(BaseModel):
    """
    Base schema for API usage information, including endpoint, units, and cost.
    """
    api_name: str
    endpoint: str
    units_used: Annotated[int, conint(ge=0)]
    cost_usd: Annotated[Decimal, condecimal(max_digits=10, decimal_places=4)]
    api_key_used: str

class ApiUsageCreate(ApiUsageBase):
    """
    Schema for creating a new API usage record.
    """
    pass

class ApiUsageUpdate(BaseModel):
    """
    Schema for updating API usage units or cost.
    """
    units_used: Optional[Annotated[int, conint(ge=0)]] = None
    cost_usd: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=4)]] = None

class ApiUsageInDB(ApiUsageBase):
    """
    Schema for API usage data as stored in the database, including IDs and timestamps.
    """
    usage_id: UUID4
    user_id: UUID4
    status_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ApiUsageResponse(ApiUsageInDB):
    """
    Schema for API usage response, inherits from ApiUsageInDB.
    """
    pass 