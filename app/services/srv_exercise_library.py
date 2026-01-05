from fastapi import Depends
from app.repository.repo_exercise_library import ExerciseLibraryRepository
from app.schemas.sche_exercise_library import ExerciseLibraryCreateRequest, ExerciseLibraryResponse

class ExerciseLibraryService:
    def __init__(self, exercise_repo: ExerciseLibraryRepository = Depends()):
        self.exercise_repo = exercise_repo

    def create_exercise(self, exercise_data: ExerciseLibraryCreateRequest) -> ExerciseLibraryResponse:
        exercise = self.exercise_repo.create(exercise_data)
        return ExerciseLibraryResponse.from_orm(exercise)
