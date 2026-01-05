from typing import Any
from fastapi import APIRouter, Depends

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest, MedicationLibraryResponse
from app.services.srv_medication_library import MedicationLibraryService

router = APIRouter()

@router.post('', dependencies=[Depends(login_required)], response_model=DataResponse[MedicationLibraryResponse])
def create_medication(
    medication_data: MedicationLibraryCreateRequest,
    medication_service: MedicationLibraryService = Depends()
) -> Any:
    try:
        medication = medication_service.create_medication(medication_data)
        return DataResponse().success_response(data=medication)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
