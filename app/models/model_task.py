from sqlalchemy import Column, String, Date, Time, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class Task(Base):
    __tablename__ = "task"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    care_plan_id = Column(UUID(as_uuid=True), ForeignKey("care_plan.care_plan_id", ondelete="CASCADE"), nullable=False)
    owner_type = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    task_date = Column(Date, nullable=False)
    task_time = Column(Time, nullable=False)
    task_type = Column(String(20), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medication_library.medication_id", ondelete="SET NULL"))
    nutrition_id = Column(UUID(as_uuid=True), ForeignKey("nutrition_library.nutrition_id", ondelete="SET NULL"))
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercise_library.exercise_id", ondelete="SET NULL"))
    status = Column(String(20), default='PENDING')
    linked_task_id = Column(UUID(as_uuid=True), ForeignKey("task.task_id", ondelete="SET NULL"))

    medication = relationship("MedicationLibrary", foreign_keys=[medication_id], lazy="joined")
