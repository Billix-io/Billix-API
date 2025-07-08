from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database import Base
from datetime import datetime

class UserUsage(Base):
    """
    SQLAlchemy model for user usage, matching the database schema in the image.
    """
    __tablename__ = "user_usage"

    id = Column(Text, primary_key=True, nullable=False)
    userId = Column(Text, ForeignKey('User.id'), nullable=False)
    chatUsage = Column(Integer, nullable=False, default=0)
    invoiceUsage = Column(Integer, nullable=False, default=0)
    resetDate = Column(DateTime, nullable=False, default=datetime.utcnow)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) 