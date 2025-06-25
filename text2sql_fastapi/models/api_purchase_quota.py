from sqlalchemy import Column, String, Numeric, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
from datetime import datetime
from database import Base

class ApiPurchaseQuota(Base):
    __tablename__ = "api_purchase_quota"

    quota_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_name = Column(String, nullable=False)
    purchase_amount_usd = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    notes = Column(String, nullable=True) 