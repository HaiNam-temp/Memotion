from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class ExerciseLibrary(Base):
    __tablename__ = "exercise_library"

    exercise_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    target_body_region = Column(String(255))
    description = Column(Text)
    duration_minutes = Column(Integer)
    difficulty_level = Column(Integer)
    video_path = Column(String(255))
