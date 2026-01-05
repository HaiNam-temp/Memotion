from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.model_exercise_library import ExerciseLibrary
from app.schemas.sche_exercise_library import ExerciseLibraryCreateRequest

class ExerciseLibraryRepository:
    def __init__(self, db_session: Session = Depends(get_db)):
        self.db = db_session

    def create(self, exercise_data: ExerciseLibraryCreateRequest) -> ExerciseLibrary:
        exercise = ExerciseLibrary(**exercise_data.dict())
        self.db.add(exercise)
        self.db.commit()
        self.db.refresh(exercise)
        return exercise

    def get_by_id(self, exercise_id: str) -> Optional[ExerciseLibrary]:
        return self.db.query(ExerciseLibrary).filter(ExerciseLibrary.exercise_id == exercise_id).first()
