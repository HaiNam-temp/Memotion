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
    """
    Create patient general profile by caretaker.
    
    This API is used by caretakers to create profiles for their assigned patients,
    since patients may have difficulty using mobile devices.
    
    Business logic:
    1. Find the patient assigned to the current caretaker user
    2. Check if the patient already has a profile (throws exception if exists)
    3. Create the profile for the assigned patient
    """
    try:
        logger.info(f"create_general_profile request: caretaker_id={current_user.user_id}, data={profile_data.dict()}")
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
    """
    Retrieve patient general profile.
    
    This API allows patients to view their own profile or caretakers to view the profile 
    of their assigned patient, including personal and medical information.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient profile
    2. Retrieves patient profile from database
    
    **Response**: Complete patient profile details.
    """
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
    """
    Update patient general profile.
    
    This API allows patients to update their own profile or caretakers to update the profile 
    of their assigned patient with new health information and personal details.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient profile
    2. Updates patient profile in database
    3. Returns updated profile details
    
    **Response**: Updated patient profile details.
    """
    try:
        logger.info(f"update_general_profile request: user_id={current_user.user_id}, data={profile_data.dict()}")
        profile = profile_service.update_patient_profile(profile_data, current_user)
        logger.info(f"update_general_profile success: profile_id={profile.patient_id}")
        return DataResponse().success_response(data=profile)
    except Exception as e:
        logger.error(f"update_general_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.delete('/general', dependencies=[Depends(login_required)], response_model=DataResponse[None])
def delete_general_profile(
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Delete patient general profile.
    
    This API allows patients to delete their own profile or caretakers to delete the profile 
    of their assigned patient, removing all associated health information.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient profile
    2. Deletes patient profile from database
    
    **Response**: Confirmation of successful deletion.
    """
    try:
        logger.info(f"delete_general_profile request: user_id={current_user.user_id}")
        profile_service.delete_patient_profile(current_user)
        logger.info(f"delete_general_profile success: user_id={current_user.user_id}")
        return DataResponse().success_response(data=None, message="Profile deleted successfully")
    except Exception as e:
        logger.error(f"delete_general_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[PhysicalTherapyResponse])
def create_physical_therapy_profile(
    therapy_data: PhysicalTherapyCreateRequest, 
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Create patient physical therapy profile by caretaker.
    
    This API allows caretakers to create physical therapy profiles for their assigned patients, 
    including therapy history, current conditions, and rehabilitation goals.
    
    **Authorization**: CARETAKER role required.
    
    **Process**:
    1. Validates caretaker has assigned patient
    2. Checks if patient already has physical therapy profile
    3. Creates new physical therapy profile in database
    
    **Response**: Details of the created physical therapy profile.
    """
    try:
        logger.info(f"create_physical_therapy_profile request: caretaker_id={current_user.user_id}")
        therapy = profile_service.create_physical_therapy_profile(therapy_data, current_user)
        logger.info(f"create_physical_therapy_profile success: therapy_id={therapy.profile_id}")
        return DataResponse().success_response(data=therapy)
    except Exception as e:
        logger.error(f"create_physical_therapy_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[PhysicalTherapyResponse])
def get_physical_therapy_profile(
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve patient physical therapy profile.
    
    This API allows patients to view their own physical therapy profile or caretakers to view 
    the profile of their assigned patient, including therapy history and current conditions.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient physical therapy profile
    2. Retrieves physical therapy profile from database
    
    **Response**: Complete physical therapy profile details.
    """
    try:
        logger.info(f"get_physical_therapy_profile request: user_id={current_user.user_id}")
        therapy = profile_service.get_physical_therapy_profile(current_user)
        logger.info(f"get_physical_therapy_profile success: therapy_id={therapy.profile_id if therapy else 'None'}")
        return DataResponse().success_response(data=therapy)
    except Exception as e:
        logger.error(f"get_physical_therapy_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.put('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[PhysicalTherapyResponse])
def update_physical_therapy_profile(
    therapy_data: PhysicalTherapyUpdateRequest,
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Update patient physical therapy profile.
    
    This API allows patients to update their own physical therapy profile or caretakers to update 
    the profile of their assigned patient with new therapy information and progress.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient physical therapy profile
    2. Updates physical therapy profile in database
    3. Returns updated profile details
    
    **Response**: Updated physical therapy profile details.
    """
    try:
        logger.info(f"update_physical_therapy_profile request: user_id={current_user.user_id}")
        therapy = profile_service.update_physical_therapy_profile(therapy_data, current_user)
        logger.info(f"update_physical_therapy_profile success: therapy_id={therapy.profile_id}")
        return DataResponse().success_response(data=therapy)
    except Exception as e:
        logger.error(f"update_physical_therapy_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.delete('/physical-therapy', dependencies=[Depends(login_required)], response_model=DataResponse[None])
def delete_physical_therapy_profile(
    profile_service: PatientProfileService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Delete patient physical therapy profile.
    
    This API allows patients to delete their own physical therapy profile or caretakers to delete 
    the profile of their assigned patient, removing all associated therapy information.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient physical therapy profile
    2. Deletes physical therapy profile from database
    
    **Response**: Confirmation of successful deletion.
    """
    try:
        logger.info(f"delete_physical_therapy_profile request: user_id={current_user.user_id}")
        profile_service.delete_physical_therapy_profile(current_user)
        logger.info(f"delete_physical_therapy_profile success: user_id={current_user.user_id}")
        return DataResponse().success_response(data=None, message="Physical therapy profile deleted successfully")
    except Exception as e:
        logger.error(f"delete_physical_therapy_profile error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))
