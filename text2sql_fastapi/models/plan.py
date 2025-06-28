from sqlalchemy import Column, Integer, String, Float
from database import Base
import uuid
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

class Plan(Base):
    __tablename__ = "plan"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    tokens = Column(Integer, nullable=False)  # Number of tokens this plan provides 