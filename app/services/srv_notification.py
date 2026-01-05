from typing import List
from fastapi import Depends
from app.repository.repo_notification import NotificationRepository
from app.models.model_user import User
from app.schemas.sche_notification import NotificationResponse

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository = Depends()):
        self.notification_repo = notification_repo

    def get_user_notifications(self, current_user: User) -> List[NotificationResponse]:
        notifications = self.notification_repo.get_by_user_id(current_user.user_id)
        return [NotificationResponse.from_orm(n) for n in notifications]
