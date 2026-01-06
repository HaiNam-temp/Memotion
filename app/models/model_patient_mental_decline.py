from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base

class PatientMentalDecline(Base):
    __tablename__ = "patient_mental_decline"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("patient_profile.profile_id", ondelete="CASCADE"), primary_key=True)
    mmse_score = Column(Integer)
    previous_illness = Column(String(255))
    previous_treatments = Column(String(255))
    functional_assessment_staging_test_score = Column(Integer)
    memory_issue = Column(String(255))
    orientation_issue = Column(String(255))
    community_affairs = Column(String(255))
    home_relationship = Column(String(255))
    daily_function_can_do = Column(String(255))
    daily_function_need_help = Column(String(255))
    behavior_change = Column(String(255))
    doctor_recommended = Column(Text)
    doctor_treatment_plan = Column(Text)
    note = Column(Text)
