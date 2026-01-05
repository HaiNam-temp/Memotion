from fastapi import Depends
from app.repository.repo_medication_library import MedicationLibraryRepository
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest, MedicationLibraryResponse

class MedicationLibraryService:
    def __init__(self, medication_repo: MedicationLibraryRepository = Depends()):
        self.medication_repo = medication_repo

    def create_medication(self, medication_data: MedicationLibraryCreateRequest) -> MedicationLibraryResponse:
        medication = self.medication_repo.create(medication_data)
        return MedicationLibraryResponse.from_orm(medication)
