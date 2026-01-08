from fastapi import Depends
from typing import List
from app.repository.repo_nutrition_library import NutritionLibraryRepository
from app.schemas.sche_nutrition_library import NutritionLibraryCreateRequest, NutritionLibraryResponse

class NutritionLibraryService:
    def __init__(self, nutrition_repo: NutritionLibraryRepository = Depends()):
        self.nutrition_repo = nutrition_repo

    def create_nutrition(self, nutrition_data: NutritionLibraryCreateRequest) -> NutritionLibraryResponse:
        nutrition = self.nutrition_repo.create(nutrition_data)
        return NutritionLibraryResponse.from_orm(nutrition)

    def get_all_nutritions(self, limit: int = 50) -> List[NutritionLibraryResponse]:
        nutritions = self.nutrition_repo.get_all(limit=limit)
        return [NutritionLibraryResponse.from_orm(n) for n in nutritions]
