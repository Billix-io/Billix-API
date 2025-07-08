from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class UserSubscription(Base):
    """
    SQLAlchemy model for subscriptions, matching the latest database schema and Pydantic schema.
    Includes foreign key relationships to User and Plan.
    """
    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    orderId = Column(Integer, nullable=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    statusFormatted = Column(Text, nullable=False)
    renewsAt = Column(Text, nullable=True)
    endsAt = Column(Text, nullable=True)
    trialEndsAt = Column(Text, nullable=True)
    price = Column(Text, nullable=False)
    isUsageBased = Column(Boolean, nullable=False, default=False)
    isPaused = Column(Boolean, nullable=False, default=False)
    subscriptionItemId = Column(Integer, nullable=False, autoincrement=True)

    # Foreign keys
    userId = Column(Text, ForeignKey('User.id'), nullable=False)
    planId = Column(Integer, ForeignKey('plan.id'), nullable=False)

    cancelUrl = Column(Text, nullable=True)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    paddleCustomerId = Column(Text, nullable=True)
    paddlePriceId = Column(Text, nullable=True)
    paddleProductId = Column(Text, nullable=True)
    paddleSubscriptionId = Column(Text, nullable=True)
    paddleTransactionId = Column(Text, nullable=True)
    provider = Column(Text, nullable=False, default='lemonsqueezy')
    updateUrl = Column(Text, nullable=True)
    updatedAt = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

   
