from typing import Any, List
from fastapi import APIRouter, Depends
import logging

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_exercise_library import ExerciseLibraryCreateRequest, ExerciseLibraryResponse
from app.services.srv_exercise_library import ExerciseLibraryService

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get('', dependencies=[Depends(login_required)], response_model=DataResponse[List[ExerciseLibraryResponse]])
def get_all_exercises(
    exercise_service: ExerciseLibraryService = Depends()
) -> Any:
    """
    Retrieve all exercises from the exercise library.
    
    This API returns a complete list of available exercises that can be used in care plans, 
    including details such as exercise name, description, difficulty level, and target muscle groups.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Fetch all exercise records from database
    2. Format exercise data for response
    
    **Response**: List of exercise items with complete details.
    """
    try:
        logger.info("get_all_exercises request")
        exercises = exercise_service.get_all_exercises()
        logger.info(f"get_all_exercises success: {len(exercises)} exercises retrieved")
        return DataResponse().success_response(data=exercises)
    except Exception as e:
        logger.error(f"get_all_exercises error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('', dependencies=[Depends(login_required)], response_model=DataResponse[ExerciseLibraryResponse])
def create_exercise(
    exercise_data: ExerciseLibraryCreateRequest,
    exercise_service: ExerciseLibraryService = Depends()
) -> Any:
    """
    Create a new exercise in the exercise library.
    
    This API allows adding new exercises to the system library, which can then be used 
    in personalized care plans. The exercise includes details like name, description, 
    instructions, difficulty, and target areas.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Validate exercise data input
    2. Create new exercise record in database
    3. Return created exercise details
    
    **Response**: Details of the newly created exercise.
    """
    try:
        logger.info(f"create_exercise request: {exercise_data.name}")
        exercise = exercise_service.create_exercise(exercise_data)
        logger.info(f"create_exercise success: exercise_id={exercise.exercise_id}")
        return DataResponse().success_response(data=exercise)
    except Exception as e:
        logger.error(f"create_exercise error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.delete('/{exercise_id}', dependencies=[Depends(login_required)], response_model=DataResponse[bool])
def delete_exercise(
    exercise_id: str,
    exercise_service: ExerciseLibraryService = Depends()
) -> Any:
    """
    Delete an exercise from the exercise library.
    
    This API allows removing exercises from the system library. The exercise will no longer 
    be available for use in care plans.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Validate exercise exists
    2. Delete exercise record from database
    3. Return deletion status
    
    **Response**: Boolean indicating success of deletion.
    """
    try:
        logger.info(f"delete_exercise request: exercise_id={exercise_id}")
        success = exercise_service.delete_exercise(exercise_id)
        if success:
            logger.info(f"delete_exercise success: exercise_id={exercise_id}")
            return DataResponse().success_response(data=True)
        else:
            logger.warning(f"delete_exercise not found: exercise_id={exercise_id}")
            raise CustomException(http_code=404, code='404', message="Exercise not found")
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"delete_exercise error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))
