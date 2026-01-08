from typing import Optional
from fastapi import Depends
from app.db.base import get_db
from app.models.model_patient_profile import PatientProfile
from app.models.model_patient_physical_therapy import PatientPhysicalTherapy

class PatientProfileRepository:
    def __init__(self, db_session = Depends(get_db)):
        self.db = db_session

    def create_profile(self, profile_data: PatientProfile) -> PatientProfile:
        self.db.add(profile_data)
        self.db.commit()
        self.db.refresh(profile_data)
        return profile_data

    def get_profile_by_patient_id(self, patient_id: str) -> Optional[PatientProfile]:
        return self.db.query(PatientProfile).filter(PatientProfile.patient_id == patient_id).first()

    def update_profile(self, profile: PatientProfile) -> PatientProfile:
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def create_physical_therapy(self, therapy_data: PatientPhysicalTherapy) -> PatientPhysicalTherapy:
        self.db.add(therapy_data)
        self.db.commit()
        self.db.refresh(therapy_data)
        return therapy_data

    def get_physical_therapy_by_patient_id(self, patient_id: str) -> Optional[PatientPhysicalTherapy]:
        profile = self.get_profile_by_patient_id(patient_id)
        if profile and profile.physical_therapy_id:
            return self.db.query(PatientPhysicalTherapy).filter(PatientPhysicalTherapy.profile_id == profile.physical_therapy_id).first()
        return None

    def update_physical_therapy(self, therapy: PatientPhysicalTherapy) -> PatientPhysicalTherapy:
        self.db.commit()
        self.db.refresh(therapy)
        return therapy
