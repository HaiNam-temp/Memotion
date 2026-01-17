from sqlalchemy import Column, String, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(50))
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    is_first_login = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
