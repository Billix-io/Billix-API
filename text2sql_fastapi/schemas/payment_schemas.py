from pydantic import BaseModel, UUID4, condecimal
from typing import Optional
from datetime import datetime
from decimal import Decimal
from models.payment import PaymentStatus, PaymentProvider

class PaymentBase(BaseModel):
    plan_id: UUID4
    amount: condecimal(max_digits=10, decimal_places=2)
    currency: str = "USD"
    provider: PaymentProvider
    transaction_id: str

class PaymentCreate(PaymentBase):
    user_id: UUID4  # ✅ Changed from int to UUID4
    status: PaymentStatus = PaymentStatus.PENDING

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None

class PaymentInDB(PaymentBase):
    payment_id: UUID4
    status: PaymentStatus
    user_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentResponse(PaymentInDB):
    pass 