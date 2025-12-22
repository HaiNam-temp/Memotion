from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base

class PatientLoneliness(Base):
    __tablename__ = "patient_loneliness"

    profile_id = Column(UUID(as_uuid=True), ForeignKey("patient_profile.profile_id", ondelete="CASCADE"), primary_key=True)
    previous_illness = Column(String(255))
    lsns6_family_score = Column(Integer)
    lsns6_friends_score = Column(Integer)
    ucla_loneliness_score = Column(Integer)
    gds15_score = Column(Integer)
    mood_status = Column(String(50))
    behavior_change_note = Column(String(255))
    note = Column(Text)
