from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
import uuid

class HelpAndSupport(Base):
    __tablename__ = "help_and_support"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name=Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, server_default=text("now()"))
    updated_at = Column(DateTime, server_default=text("now()"), onupdate=text("now()"))

  
