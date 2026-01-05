from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.model_nutrition_library import NutritionLibrary
from app.schemas.sche_nutrition_library import NutritionLibraryCreateRequest

class NutritionLibraryRepository:
    def __init__(self, db_session: Session = Depends(get_db)):
        self.db = db_session

    def create(self, nutrition_data: NutritionLibraryCreateRequest) -> NutritionLibrary:
        nutrition = NutritionLibrary(**nutrition_data.dict())
        self.db.add(nutrition)
        self.db.commit()
        self.db.refresh(nutrition)
        return nutrition

    def get_by_id(self, nutrition_id: str) -> Optional[NutritionLibrary]:
        return self.db.query(NutritionLibrary).filter(NutritionLibrary.nutrition_id == nutrition_id).first()
