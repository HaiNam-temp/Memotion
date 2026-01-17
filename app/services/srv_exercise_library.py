from fastapi import Depends
from typing import List, Optional
from app.repository.repo_exercise_library import ExerciseLibraryRepository
from app.schemas.sche_exercise_library import ExerciseLibraryCreateRequest, ExerciseLibraryResponse

class ExerciseLibraryService:
    def __init__(self, exercise_repo: ExerciseLibraryRepository = Depends()):
        self.exercise_repo = exercise_repo

    def create_exercise(self, exercise_data: ExerciseLibraryCreateRequest) -> ExerciseLibraryResponse:
        exercise = self.exercise_repo.create(exercise_data)
        return ExerciseLibraryResponse.from_orm(exercise)

    def get_all_exercises(self, limit: int = 50) -> List[ExerciseLibraryResponse]:
        exercises = self.exercise_repo.get_all(limit=limit)
        return [ExerciseLibraryResponse.from_orm(e) for e in exercises]

    def get_exercise_by_id(self, exercise_id: str) -> Optional[ExerciseLibraryResponse]:
        exercise = self.exercise_repo.get_by_id(exercise_id)
        if exercise:
            return ExerciseLibraryResponse.from_orm(exercise)
        return None
