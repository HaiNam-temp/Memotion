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
        raise CustomException(http_code=400, code='400', message=str(e))


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


@router.put("/role", dependencies=[Depends(login_required)], response_model=DataResponse[UserItemResponse])
def update_user_role(current_user: User = Depends(UserService.get_current_user),
                     user_service: UserService = Depends()) -> Any:
    """
    API Update user role.
    
    This API allows users to change their role from PATIENT to CARETAKER.
    Role can only be changed in one direction: PATIENT -> CARETAKER.
    No request body needed - automatically upgrades from PATIENT to CARETAKER.
    Uses the authenticated user's ID from the token.
    
    **Authorization**: Authenticated user required.
    
    **Restrictions**:
    - Users can only update their own role
    - Role can only be changed from PATIENT to CARETAKER
    - Cannot change from CARETAKER back to PATIENT
    
    **Process**:
    1. Get user ID from authentication token
    2. Check that current role is PATIENT
    3. Automatically set role to CARETAKER
    4. Update user role
    5. Return updated user information
    """
    try:
        updated_user = user_service.update_user_role(
            user_id=str(current_user.user_id),
            current_user=current_user
        )
        return DataResponse().success_response(data=updated_user)
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"update_user_role error: {str(e)}", exc_info=True)
        raise CustomException(http_code=500, code='500', message=str(e))
