from sqlalchemy import Column, Integer, String, Float
from database import Base
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

class Plan(Base):
    __tablename__ = "plan"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    monthlyPrice = Column(Float, nullable=False)
    yearlyPrice = Column(Float, nullable=False)
    priceId = Column(String,nullable=False)  # Stripe or payment provider price id
    features = Column(JSONB, nullable=False)  # List of feature dicts, e.g. [{"text": "..."}]
    tokens = Column(Integer, nullable=False)  # Number of tokens this plan provides 