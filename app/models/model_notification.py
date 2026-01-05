from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.model_base import Base
import uuid

class Notification(Base):
    __tablename__ = "notification"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("task.task_id"))
    type = Column(String(50), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    task = relationship("Task", foreign_keys=[task_id], lazy="joined")
