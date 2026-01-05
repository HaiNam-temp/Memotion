from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.schemas.sche_task import TaskResponse

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

class NotificationResponse(NotificationBase):
    notification_id: UUID
    user_id: UUID
    task_id: Optional[UUID] = None
    task: Optional[TaskResponse] = None

    class Config:
        orm_mode = True
