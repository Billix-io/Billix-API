from pydantic import BaseModel, UUID4, condecimal, conint
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal

class ApiPurchaseQuotaBase(BaseModel):
    api_name: str
    purchase_amount_usd: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2)]
    token_purchased: Annotated[int, conint(gt=0)]
    notes: Optional[str] = None

class ApiPurchaseQuotaCreate(ApiPurchaseQuotaBase):
    pass

class ApiPurchaseQuotaUpdate(BaseModel):
    purchase_amount_usd: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2)]] = None
    notes: Optional[str] = None

class ApiPurchaseQuotaInDB(ApiPurchaseQuotaBase):
    quota_id: UUID4
    purchase_date: datetime

    class Config:
        from_attributes = True

class ApiPurchaseQuotaResponse(ApiPurchaseQuotaInDB):
    pass 