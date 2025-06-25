from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid

class Tool(Base):
    __tablename__ = 'tools'

    tool_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tool_config = Column(JSONB, nullable=True)  # JSONB for tool parameters or template
    sql_template = Column(Text, nullable=True)  # SQL template with placeholders
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()) 