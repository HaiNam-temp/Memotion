from fastapi import Depends
from typing import List
from app.repository.repo_medication_library import MedicationLibraryRepository
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest, MedicationLibraryResponse

class MedicationLibraryService:
    def __init__(self, medication_repo: MedicationLibraryRepository = Depends()):
        self.medication_repo = medication_repo

    def create_medication(self, medication_data: MedicationLibraryCreateRequest) -> MedicationLibraryResponse:
        medication = self.medication_repo.create(medication_data)
        return MedicationLibraryResponse.from_orm(medication)

    def get_all_medications(self, limit: int = 50) -> List[MedicationLibraryResponse]:
        medications = self.medication_repo.get_all(limit=limit)
        return [MedicationLibraryResponse.from_orm(m) for m in medications]
