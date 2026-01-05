from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class NutritionLibraryBase(BaseModel):
    name: str
    calories: Optional[int] = None
    description: Optional[str] = None
    meal_type: Optional[str] = None
    image_path: Optional[str] = None

class NutritionLibraryCreateRequest(NutritionLibraryBase):
    pass

class NutritionLibraryResponse(NutritionLibraryBase):
    nutrition_id: UUID

    class Config:
        orm_mode = True
