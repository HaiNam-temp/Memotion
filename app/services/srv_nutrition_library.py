from fastapi import Depends
from app.repository.repo_nutrition_library import NutritionLibraryRepository
from app.schemas.sche_nutrition_library import NutritionLibraryCreateRequest, NutritionLibraryResponse

class NutritionLibraryService:
    def __init__(self, nutrition_repo: NutritionLibraryRepository = Depends()):
        self.nutrition_repo = nutrition_repo

    def create_nutrition(self, nutrition_data: NutritionLibraryCreateRequest) -> NutritionLibraryResponse:
        nutrition = self.nutrition_repo.create(nutrition_data)
        return NutritionLibraryResponse.from_orm(nutrition)
