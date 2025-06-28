from sqlalchemy import Column, String, TIMESTAMP, Enum, ForeignKey, UniqueConstraint, CheckConstraint, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    google_id = Column(String(255), nullable=True, unique=True)
    phone_number = Column(String(255), nullable=True, unique=True)
    otp_code = Column(String(255), nullable=True)
    otp_expiry = Column(TIMESTAMP, nullable=True)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.role_id'), nullable=True)

    status_active = Column(Boolean, nullable=False, server_default=text('true'))
    is_verified = Column(Boolean, nullable=False, server_default=text('false'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user_databases = relationship("UserDatabase", back_populates="user")
    role = relationship("Role", back_populates="users", lazy="selectin")
    payments = relationship("Payment", back_populates="user")
    api_usages = relationship("ApiUsage", back_populates="user")
    subscription = relationship("UserSubscription", back_populates="user", uselist=False)
    api_keys = relationship("UsersApiKey", back_populates="user")

    # Constraints
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('google_id', name='uq_user_google_id'),
        UniqueConstraint('phone_number', name='uq_user_phone_number'),
        CheckConstraint("char_length(otp_code) = 6 OR otp_code IS NULL", name="check_otp_code_length"),
        CheckConstraint("char_length(first_name) > 0", name="check_first_name_not_empty"),
        CheckConstraint("char_length(last_name) > 0", name="check_last_name_not_empty"),
    )