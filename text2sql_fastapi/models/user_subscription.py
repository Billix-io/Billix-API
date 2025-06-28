from sqlalchemy import Column, Numeric, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class UserSubscription(Base):
    __tablename__ = "user_subscription"

    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plan.plan_id"), nullable=False)
    total_tokens_purchased = Column(Numeric(20, 0), nullable=False)
    tokens_remaining = Column(Numeric(20, 0), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="subscription")
   