from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.model_notification import Notification

class NotificationRepository:
    def __init__(self, db_session: Session = Depends(get_db)):
        self.db = db_session

    def get_by_user_id(self, user_id: str) -> List[Notification]:
        return self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).all()
