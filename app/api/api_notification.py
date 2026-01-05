from typing import Any, List
from fastapi import APIRouter, Depends

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_notification import NotificationResponse
from app.services.srv_notification import NotificationService
from app.services.srv_user import UserService
from app.models.model_user import User

router = APIRouter()

@router.get('', dependencies=[Depends(login_required)], response_model=DataResponse[List[NotificationResponse]])
def get_notifications(
    notification_service: NotificationService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        notifications = notification_service.get_user_notifications(current_user)
        return DataResponse().success_response(data=notifications)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
