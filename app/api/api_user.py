import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_user import UserItemResponse, UserUpdateMeRequest
from app.services.srv_user import UserService
from app.models.model_user import User

logger = logging.getLogger()
router = APIRouter()


@router.get("", dependencies=[Depends(login_required)], response_model=DataResponse[List[UserItemResponse]])
def get(user_service: UserService = Depends()) -> Any:
    """
    API Get list User
    """
    try:
        users = user_service.get_users()
        return DataResponse().success_response(data=users)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))


@router.get("/me", dependencies=[Depends(login_required)], response_model=DataResponse[UserItemResponse])
def detail_me(current_user: User = Depends(UserService.get_current_user)) -> Any:
    """
    API get detail current User
    """
    return DataResponse().success_response(data=current_user)


@router.put("/me", dependencies=[Depends(login_required)], response_model=DataResponse[UserItemResponse])
def update_me(user_data: UserUpdateMeRequest,
              current_user: User = Depends(UserService.get_current_user),
              user_service: UserService = Depends()) -> Any:
    """
    API Update current User
    """
    try:
        updated_user = user_service.update_me(data=user_data, current_user=current_user)
        return DataResponse().success_response(data=updated_user)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))


@router.get("/{user_id}", dependencies=[Depends(login_required)], response_model=DataResponse[UserItemResponse])
def detail(user_id: str, user_service: UserService = Depends()) -> Any:
    """
    API get Detail User
    """
    try:
        return DataResponse().success_response(data=user_service.get(user_id))
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
