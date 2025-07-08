from sqlalchemy import Column, Text, DateTime
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class User(Base):
    """
    SQLAlchemy model for the User table, matching the provided database schema image.
    Only includes columns present in the image.
    """
    __tablename__ = 'User'

    id = Column(Text, primary_key=True, nullable=False)
    clerkId = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    firstName = Column(Text, nullable=True)
    lastName = Column(Text, nullable=True)
    profileImageUrl = Column(Text, nullable=True)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = Column(Text, nullable=False, default='USER')  # Should match "UserRole" enum in DB
    lastActive = Column(DateTime, nullable=True)
    status = Column(Text, nullable=False, default='ACTIVE')  # Should match "UserStatus" enum in DB

    api_keys= relationship("UsersApiKey", back_populates="user") 
    api_usages=relationship("ApiUsage", back_populates="user") 