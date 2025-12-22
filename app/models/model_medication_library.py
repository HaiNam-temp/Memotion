from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class MedicationLibrary(Base):
    __tablename__ = "medication_library"

    medication_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    description = Column(Text)
    dosage = Column(String(255))
    frequency_per_day = Column(Integer)
    notes = Column(Text)
    image_path = Column(String(255))
