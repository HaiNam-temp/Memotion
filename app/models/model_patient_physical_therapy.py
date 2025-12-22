from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base

class PatientPhysicalTherapy(Base):
    __tablename__ = "patient_physical_therapy"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("patient_profile.profile_id", ondelete="CASCADE"), primary_key=True)
    pain_location = Column(String(255))
    pain_scale_score = Column(Integer)
    pain_character = Column(String(255))
    pain_assessment = Column(String(255))
    muscle_tone = Column(String(255))
    muscle_strength = Column(String(255))
    balanced_valuation = Column(String(255))
    fall_risk = Column(String(255))
    self_stand_ability = Column(String(100))
    tug_time = Column(Integer)
    previous_illness = Column(String(255))
    previous_treatments = Column(String(255))
    daily_actities = Column(String(255))
    doctor_recommended = Column(Text)
    doctor_treatment_plan = Column(Text)
    note = Column(Text)
