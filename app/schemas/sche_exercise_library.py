from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class ExerciseLibraryBase(BaseModel):
    name: str
    target_body_region: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    difficulty_level: Optional[int] = None
    video_path: Optional[str] = None

class ExerciseLibraryCreateRequest(ExerciseLibraryBase):
    pass

class ExerciseLibraryResponse(ExerciseLibraryBase):
    exercise_id: UUID

    class Config:
        orm_mode = True
