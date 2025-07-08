from sqlalchemy import Column, Integer, String, Boolean, Text
from database import Base

class Plan(Base):
    """
    SQLAlchemy model for plans, matching the latest database schema and Pydantic schema.
    """
    __tablename__ = "plan"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    productId = Column(Integer, nullable=False)
    productName = Column(Text, nullable=True)
    variantId = Column(Integer, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Text, nullable=False)
    isUsageBased = Column(Boolean, nullable=False, default=False)
    interval = Column(Text, nullable=True)
    intervalCount = Column(Integer, nullable=True)
    trialInterval = Column(Text, nullable=True)
    trialIntervalCount = Column(Integer, nullable=True)
    sort = Column(Integer, nullable=True)
    paddlePriceId = Column(Text, nullable=True)
    chatLimit = Column(Integer, nullable=True)
    invoiceLimit = Column(Integer, nullable=True) 