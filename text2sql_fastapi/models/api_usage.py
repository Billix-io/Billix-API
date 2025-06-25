from sqlalchemy import Column, String, Numeric, DateTime, BigInteger, ForeignKey, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

class ApiUsage(Base):
    __tablename__ = "api_usage"

    usage_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    api_name = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    units_used = Column(BigInteger, nullable=False)
    cost_usd = Column(Numeric(10, 4), nullable=False)
    api_key_used = Column(String, nullable=False)
    status_active = Column(Boolean, nullable=False, server_default=text('true'))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="api_usages") 