from sqlalchemy import Column, String, TIMESTAMP, Enum,Integer, ForeignKey, UniqueConstraint, CheckConstraint, text, Boolean, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum
from database import Base
from sqlalchemy.sql import func

class PaymentStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"

class PaymentProvider(str, enum.Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    plan_id = Column(Integer, ForeignKey('plan.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(Enum(PaymentStatus, name="payment_status_enum", schema="public"), nullable=False)
    provider = Column(Enum(PaymentProvider, name="payment_provider_enum", schema="public"), nullable=False)
    transaction_id = Column(String(255), nullable=False, unique=True)
    user_id = Column(Text, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)

    

    def __repr__(self):
        return f"<Payment {self.payment_id}: {self.amount} {self.currency}>"