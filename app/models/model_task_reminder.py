from sqlalchemy import Column, String, DateTime, ForeignKey, Interval, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class TaskReminder(Base):
    __tablename__ = "task_reminder"

    reminder_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("task.task_id", ondelete="CASCADE"), nullable=False)
    remind_before = Column(Interval, nullable=False)
    remind_time = Column(DateTime)
    channel = Column(String(50), nullable=False)
    status = Column(String(20), default='SCHEDULED')
    created_at = Column(DateTime, default=func.now())
