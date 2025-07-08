# text2sql_fastapi/models/api_usage.py
from sqlalchemy import Column, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    userId = Column(Text, ForeignKey('User.id'), nullable=False)
    chatUsage = Column(Integer, nullable=False, default=0)
    invoiceUsage = Column(Integer, nullable=False, default=0)
    resetDate = Column(DateTime, nullable=False, default=datetime.utcnow)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) 

    user = relationship("User", back_populates="api_usages")