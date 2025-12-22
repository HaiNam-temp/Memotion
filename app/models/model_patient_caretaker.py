from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base

class PatientCaretaker(Base):
    __tablename__ = "patient_caretaker"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    caretaker_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    assigned_at = Column(DateTime, default=func.now())
