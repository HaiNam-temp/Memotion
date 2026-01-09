from typing import Any, List
from fastapi import APIRouter, Depends
import logging

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest, MedicationLibraryResponse
from app.services.srv_medication_library import MedicationLibraryService

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get('', dependencies=[Depends(login_required)], response_model=DataResponse[List[MedicationLibraryResponse]])
def get_all_medications(
    medication_service: MedicationLibraryService = Depends()
) -> Any:
    """
    Retrieve all medications from the medication library.
    
    This API returns a complete list of available medications that can be used in care plans, 
    including details such as medication name, dosage, frequency, side effects, and usage instructions.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Fetch all medication records from database
    2. Format medication data for response
    
    **Response**: List of medication items with complete details.
    """
    try:
        logger.info("get_all_medications request")
        medications = medication_service.get_all_medications()
        logger.info(f"get_all_medications success: {len(medications)} medications retrieved")
        return DataResponse().success_response(data=medications)
    except Exception as e:
        logger.error(f"get_all_medications error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('', dependencies=[Depends(login_required)], response_model=DataResponse[MedicationLibraryResponse])
def create_medication(
    medication_data: MedicationLibraryCreateRequest,
    medication_service: MedicationLibraryService = Depends()
) -> Any:
    """
    Create a new medication in the medication library.
    
    This API allows adding new medications to the system library, which can then be used 
    in personalized care plans. The medication includes details like name, dosage, frequency, 
    side effects, and administration instructions.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Validate medication data input
    2. Create new medication record in database
    3. Return created medication details
    
    **Response**: Details of the newly created medication.
    """
    try:
        logger.info(f"create_medication request: {medication_data.name}")
        medication = medication_service.create_medication(medication_data)
        logger.info(f"create_medication success: medication_id={medication.id}")
        return DataResponse().success_response(data=medication)
    except Exception as e:
        logger.error(f"create_medication error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))
