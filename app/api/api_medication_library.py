from typing import Any, List
from fastapi import APIRouter, Depends, UploadFile, File
import logging
import os

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest, MedicationLibraryResponse, MedicationScanResponse
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
        logger.info(f"create_medication success: medication_id={medication.medication_id}")
        return DataResponse().success_response(data=medication)
    except Exception as e:
        logger.error(f"create_medication error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('/scan-image', dependencies=[Depends(login_required)], response_model=DataResponse[MedicationScanResponse])
async def scan_medication_image(
    file: UploadFile = File(...),
    medication_service: MedicationLibraryService = Depends()
) -> Any:
    """
    Scan medication image to identify and extract medication information.
    
    This API allows users to upload an image of medication packaging or pills to automatically 
    identify the medication and add it to the library if not already present.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Receive and validate uploaded image
    2. Use AI agent to scan and analyze the medication image
    3. Check if medication already exists in library by name
    4. If exists, return existing medication data
    5. If not exists, create new medication record and upload image
    6. Return medication information
    
    **Supported file types**: PNG, JPG, JPEG, GIF, WebP
    
    **Response**: MedicationScanResponse with medication details or error message if medication not found.
    """
    try:
        logger.info(f"scan_medication_image request: filename={file.filename}")

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise CustomException(http_code=400, code='400', message="Invalid file type. Only image files are allowed.")

        # Save uploaded file temporarily
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"temp_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        try:
            # Process the image
            result = medication_service.scan_and_process_medication_image(temp_file_path)
            
            logger.info(f"scan_medication_image success: medication processed")
            return DataResponse().success_response(data=MedicationScanResponse(medication=result))
                
        except CustomException as e:
            if "AI Agent" in str(e.message):
                # Agent error
                logger.error(f"scan_medication_image agent error: {str(e.message)}")
                return DataResponse().success_response(data=MedicationScanResponse(agent_error=str(e.message)))
            else:
                # Not found error
                logger.info(f"scan_medication_image: medication not found")
                return DataResponse().success_response(data=MedicationScanResponse(message="Thuốc Not found"))
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except CustomException as e:
        raise e
    except Exception as e:
        logger.error(f"scan_medication_image error: {str(e)}", exc_info=True)
        raise CustomException(http_code=500, code='500', message=str(e))

@router.delete('/{medication_id}', dependencies=[Depends(login_required)], response_model=DataResponse[bool])
def delete_medication(
    medication_id: str,
    medication_service: MedicationLibraryService = Depends()
) -> Any:
    """
    Delete a medication from the medication library.
    
    This API allows removing medications from the system library. The medication will no longer 
    be available for use in care plans.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Validate medication exists
    2. Delete medication record from database
    3. Return deletion status
    
    **Response**: Boolean indicating success of deletion.
    """
    try:
        logger.info(f"delete_medication request: medication_id={medication_id}")
        success = medication_service.delete_medication(medication_id)
        if success:
            logger.info(f"delete_medication success: medication_id={medication_id}")
            return DataResponse().success_response(data=True)
        else:
            logger.warning(f"delete_medication not found: medication_id={medication_id}")
            raise CustomException(http_code=404, code='404', message="Medication not found")
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"delete_medication error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))
