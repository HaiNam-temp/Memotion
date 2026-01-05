from typing import Any
from fastapi import APIRouter, Depends

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_exercise_library import ExerciseLibraryCreateRequest, ExerciseLibraryResponse
from app.services.srv_exercise_library import ExerciseLibraryService

router = APIRouter()

@router.post('', dependencies=[Depends(login_required)], response_model=DataResponse[ExerciseLibraryResponse])
def create_exercise(
    exercise_data: ExerciseLibraryCreateRequest,
    exercise_service: ExerciseLibraryService = Depends()
) -> Any:
    try:
        exercise = exercise_service.create_exercise(exercise_data)
        return DataResponse().success_response(data=exercise)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
