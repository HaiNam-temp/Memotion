from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class MedicationLibraryBase(BaseModel):
    name: str
    description: Optional[str] = None
    dosage: Optional[str] = None
    frequency_per_day: Optional[int] = None
    notes: Optional[str] = None
    image_path: Optional[str] = None

class MedicationLibraryCreateRequest(MedicationLibraryBase):
    pass

class MedicationLibraryResponse(MedicationLibraryBase):
    medication_id: UUID

    class Config:
        orm_mode = True
