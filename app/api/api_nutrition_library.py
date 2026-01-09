from typing import Any, List
from fastapi import APIRouter, Depends
import logging

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_nutrition_library import NutritionLibraryCreateRequest, NutritionLibraryResponse
from app.services.srv_nutrition_library import NutritionLibraryService

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get('', dependencies=[Depends(login_required)], response_model=DataResponse[List[NutritionLibraryResponse]])
def get_all_nutritions(
    nutrition_service: NutritionLibraryService = Depends()
) -> Any:
    """
    Retrieve all nutrition items from the nutrition library.
    
    This API returns a complete list of available nutrition items that can be used in care plans, 
    including details such as food name, nutritional values, serving size, calories, and dietary recommendations.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Fetch all nutrition records from database
    2. Format nutrition data for response
    
    **Response**: List of nutrition items with complete details.
    """
    try:
        logger.info("get_all_nutritions request")
        nutritions = nutrition_service.get_all_nutritions()
        logger.info(f"get_all_nutritions success: {len(nutritions)} nutrition items retrieved")
        return DataResponse().success_response(data=nutritions)
    except Exception as e:
        logger.error(f"get_all_nutritions error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('', dependencies=[Depends(login_required)], response_model=DataResponse[NutritionLibraryResponse])
def create_nutrition(
    nutrition_data: NutritionLibraryCreateRequest,
    nutrition_service: NutritionLibraryService = Depends()
) -> Any:
    """
    Create a new nutrition item in the nutrition library.
    
    This API allows adding new nutrition items to the system library, which can then be used 
    in personalized care plans. The nutrition item includes details like food name, nutritional 
    values, serving size, calories, and dietary information.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Validate nutrition data input
    2. Create new nutrition record in database
    3. Return created nutrition details
    
    **Response**: Details of the newly created nutrition item.
    """
    try:
        logger.info(f"create_nutrition request: {nutrition_data.name}")
        nutrition = nutrition_service.create_nutrition(nutrition_data)
        logger.info(f"create_nutrition success: nutrition_id={nutrition.nutrition_id}")
        return DataResponse().success_response(data=nutrition)
    except Exception as e:
        logger.error(f"create_nutrition error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.delete('/{nutrition_id}', dependencies=[Depends(login_required)], response_model=DataResponse[bool])
def delete_nutrition(
    nutrition_id: str,
    nutrition_service: NutritionLibraryService = Depends()
) -> Any:
    """
    Delete a nutrition item from the nutrition library.
    
    This API allows removing nutrition items from the system library. The nutrition item will no longer 
    be available for use in care plans.
    
    **Authorization**: Authenticated user required.
    
    **Process**:
    1. Validate nutrition item exists
    2. Delete nutrition record from database
    3. Return deletion status
    
    **Response**: Boolean indicating success of deletion.
    """
    try:
        logger.info(f"delete_nutrition request: nutrition_id={nutrition_id}")
        success = nutrition_service.delete_nutrition(nutrition_id)
        if success:
            logger.info(f"delete_nutrition success: nutrition_id={nutrition_id}")
            return DataResponse().success_response(data=True)
        else:
            logger.warning(f"delete_nutrition not found: nutrition_id={nutrition_id}")
            raise CustomException(http_code=404, code='404', message="Nutrition item not found")
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"delete_nutrition error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))
