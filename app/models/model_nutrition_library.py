from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class NutritionLibrary(Base):
    __tablename__ = "nutrition_library"

    nutrition_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    calories = Column(Integer)
    description = Column(Text)
    meal_type = Column(String(50))
    image_path = Column(String(255))
