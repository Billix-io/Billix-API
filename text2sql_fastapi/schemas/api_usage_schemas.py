from pydantic import BaseModel, UUID4, condecimal, conint
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal

class ApiUsageBase(BaseModel):
    api_name: str
    endpoint: str
    units_used: Annotated[int, conint(ge=0)]
    cost_usd: Annotated[Decimal, condecimal(max_digits=10, decimal_places=4)]
    api_key_used: str

class ApiUsageCreate(ApiUsageBase):
    pass

class ApiUsageUpdate(BaseModel):
    units_used: Optional[Annotated[int, conint(ge=0)]] = None
    cost_usd: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=4)]] = None

class ApiUsageInDB(ApiUsageBase):
    usage_id: UUID4
    user_id: UUID4
    status_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ApiUsageResponse(ApiUsageInDB):
    pass 