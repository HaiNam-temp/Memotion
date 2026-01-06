from typing import Optional


from uuid import UUID
from pydantic import BaseModel
from app.helpers.enums import DiseaseType, Gender

class PatientProfileBase(BaseModel):
    gender: Optional[Gender] = None
    living_arrangement: Optional[str] = None
    bmi_score: Optional[int] = None
    map_score: Optional[int] = None
    rhr_score: Optional[int] = None
    adl_score: Optional[int] = None
    iadl_score: Optional[int] = None
    blood_glucose_level: Optional[int] = None
    disease_type: DiseaseType
    condition_note: Optional[str] = None

class PatientProfileCreateRequest(PatientProfileBase):
    pass

class PatientProfileUpdateRequest(BaseModel):
    gender: Optional[str] = None
    living_arrangement: Optional[str] = None
    bmi_score: Optional[int] = None
    map_score: Optional[int] = None
    rhr_score: Optional[int] = None
    adl_score: Optional[int] = None
    iadl_score: Optional[int] = None
    blood_glucose_level: Optional[int] = None
    disease_type: Optional[DiseaseType] = None
    condition_note: Optional[str] = None

class PatientProfileResponse(PatientProfileBase):
    profile_id: UUID
    patient_id: UUID

    class Config:
        orm_mode = True

class PhysicalTherapyBase(BaseModel):
    pain_location: Optional[str] = None
    pain_scale_score: Optional[int] = None
    pain_character: Optional[str] = None
    pain_assessment: Optional[str] = None
    muscle_tone: Optional[str] = None
    muscle_strength: Optional[str] = None
    balanced_valuation: Optional[str] = None
    fall_risk: Optional[str] = None
    self_stand_ability: Optional[str] = None
    tug_time: Optional[int] = None
    previous_illness: Optional[str] = None
    previous_treatments: Optional[str] = None
    daily_actities: Optional[str] = None
    doctor_recommended: Optional[str] = None
    doctor_treatment_plan: Optional[str] = None
    note: Optional[str] = None

class PhysicalTherapyCreateRequest(PhysicalTherapyBase):
    pass

class PhysicalTherapyUpdateRequest(PhysicalTherapyBase):
    pass

class PhysicalTherapyResponse(PhysicalTherapyBase):
    profile_id: UUID

    class Config:
        orm_mode = True
