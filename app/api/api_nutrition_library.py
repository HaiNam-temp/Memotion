from typing import Any, List
from fastapi import APIRouter, Depends

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_nutrition_library import NutritionLibraryCreateRequest, NutritionLibraryResponse
from app.services.srv_nutrition_library import NutritionLibraryService

router = APIRouter()

@router.get('', dependencies=[Depends(login_required)], response_model=DataResponse[List[NutritionLibraryResponse]])
def get_all_nutritions(
    nutrition_service: NutritionLibraryService = Depends()
) -> Any:
    try:
        nutritions = nutrition_service.get_all_nutritions()
        return DataResponse().success_response(data=nutritions)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('', dependencies=[Depends(login_required)], response_model=DataResponse[NutritionLibraryResponse])
def create_nutrition(
    nutrition_data: NutritionLibraryCreateRequest,
    nutrition_service: NutritionLibraryService = Depends()
) -> Any:
    try:
        nutrition = nutrition_service.create_nutrition(nutrition_data)
        return DataResponse().success_response(data=nutrition)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
