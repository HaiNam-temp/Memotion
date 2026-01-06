import logging
from typing import Any
from fastapi import APIRouter, Depends

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_patient_profile import PatientProfileCreateRequest, PatientProfileResponse, PhysicalTherapyCreateRequest, PhysicalTherapyResponse, PatientProfileUpdateRequest, PhysicalTherapyUpdateRequest
from app.services.srv_patient_profile import PatientProfileService
from app.services.srv_user import UserService
from app.models.model_user import User

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post('/general', dependencies=[Depends(login_required)], response_model=DataResponse[PatientProfileResponse])
def create_general_profile(
    profile_data: PatientProfileCreateRequest, 
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        logger.info(f"create_general_profile request: user_id={current_user.user_id}, data={profile_data.dict()}")
        profile = profile_service.create_patient_profile(profile_data, current_user)
        logger.info(f"create_general_profile success: profile_id={profile.patient_id}")
        return DataResponse().success_response(data=profile)
    except Exception as e:
        logger.error(f"create_general_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/general', dependencies=[Depends(login_required)], response_model=DataResponse[PatientProfileResponse])
def get_general_profile(
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        logger.info(f"get_general_profile request: user_id={current_user.user_id}")
        profile = profile_service.get_patient_profile(current_user)
        logger.info(f"get_general_profile success: profile_id={profile.patient_id if profile else 'None'}")
        return DataResponse().success_response(data=profile)
    except Exception as e:
        logger.error(f"get_general_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.put('/general', dependencies=[Depends(login_required)], response_model=DataResponse[PatientProfileResponse])
def update_general_profile(
    profile_data: PatientProfileUpdateRequest,
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        logger.info(f"update_general_profile request: user_id={current_user.user_id}, data={profile_data.dict()}")
        profile = profile_service.update_patient_profile(profile_data, current_user)
        logger.info(f"update_general_profile success: profile_id={profile.patient_id}")
        return DataResponse().success_response(data=profile)
    except Exception as e:
        logger.error(f"update_general_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[PhysicalTherapyResponse])
def create_physical_therapy_profile(
    therapy_data: PhysicalTherapyCreateRequest, 
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        therapy = profile_service.create_physical_therapy_profile(therapy_data, current_user)
        return DataResponse().success_response(data=therapy)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[PhysicalTherapyResponse])
def get_physical_therapy_profile(
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        therapy = profile_service.get_physical_therapy_profile(current_user)
        return DataResponse().success_response(data=therapy)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))

@router.put('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[PhysicalTherapyResponse])
def update_physical_therapy_profile(
    therapy_data: PhysicalTherapyUpdateRequest,
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        therapy = profile_service.update_physical_therapy_profile(therapy_data, current_user)
        return DataResponse().success_response(data=therapy)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
