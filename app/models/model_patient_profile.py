from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class PatientProfile(Base):
    __tablename__ = "patient_profile"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    gender = Column(String(255))
    living_arrangement = Column(String(255))
    bmi_score = Column(Integer)
    map_score = Column(Integer)
    rhr_score = Column(Integer)
    adl_score = Column(Integer)
    iadl_score = Column(Integer)
    blood_glucose_level = Column(Integer)
    disease_type = Column(String(100), nullable=False)
    condition_note = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
