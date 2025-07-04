"""
Pydantic schemas for Payment models, including creation, update, and response formats.
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from models.payment import PaymentStatus, PaymentProvider

class PaymentBase(BaseModel):
    """
    Base schema for payment information, including plan, amount, currency, provider, and transaction ID.
    """
    plan_id: UUID4
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    currency: str = "USD"
    provider: PaymentProvider
    transaction_id: str

class PaymentCreate(PaymentBase):
    """
    Schema for creating a new payment, including user ID and status.
    """
    user_id: UUID4  # ✅ Changed from int to UUID4
    status: PaymentStatus = PaymentStatus.PENDING

class PaymentUpdate(BaseModel):
    """
    Schema for updating payment status or transaction ID.
    """
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None

class PaymentInDB(PaymentBase):
    """
    Schema for payment data as stored in the database, including payment ID, status, user ID, and creation time.
    """
    payment_id: UUID4
    status: PaymentStatus
    user_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentResponse(PaymentInDB):
    """
    Schema for payment response, inherits from PaymentInDB.
    """
    pass 