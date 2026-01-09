from typing import Optional, List
from fastapi import Depends
from app.db.base import get_db
from app.models.model_medication_library import MedicationLibrary
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest

class MedicationLibraryRepository:
    def __init__(self, db_session = Depends(get_db)):
        self.db = db_session

    def create(self, medication_data: MedicationLibraryCreateRequest) -> MedicationLibrary:
        medication = MedicationLibrary(**medication_data.dict())
        self.db.add(medication)
        self.db.commit()
        self.db.refresh(medication)
        return medication

    def get_by_id(self, medication_id: str) -> Optional[MedicationLibrary]:
        return self.db.query(MedicationLibrary).filter(MedicationLibrary.medication_id == medication_id).first()

    def get_all(self, limit: int = 50) -> List[MedicationLibrary]:
        return self.db.query(MedicationLibrary).limit(limit).all()

    def delete(self, medication_id: str) -> bool:
        medication = self.db.query(MedicationLibrary).filter(MedicationLibrary.medication_id == medication_id).first()
        if medication:
            self.db.delete(medication)
            self.db.commit()
            return True
        return False
