from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class HealthDailyTrack(Base):
    __tablename__ = "health_daily_track"

    track_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    track_date = Column(Date, nullable=False)
    heart_rate = Column(Integer)
    blood_pressure = Column(Integer)
    blood_sugar = Column(Float)
    mood_score = Column(Integer)
    total_tasks = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    medication_total = Column(Integer, default=0)
    medication_taken = Column(Integer, default=0)
    stress_level = Column(Integer)
    social_activity = Column(Integer)
    loneliness_score = Column(Integer)
    voice_tone = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('patient_id', 'track_date', name='uq_patient_track_date'),
    )
