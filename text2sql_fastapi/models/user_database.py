from sqlalchemy import Column, String, Integer, ForeignKey, Text, TIMESTAMP, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid

class UserDatabase(Base):
    __tablename__ = 'user_databases'

    db_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)
    db_type = Column(String(50), nullable=False)  # e.g., postgresql, mysql, etc.
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    database_name = Column(String(255), nullable=False)
    connection_status = Column(String(20), nullable=False, default='pending')  # connected / failed / pending
    last_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="user_databases") 