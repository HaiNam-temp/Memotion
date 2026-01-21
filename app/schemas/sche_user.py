from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.helpers.enums import UserRole


class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_first_login: Optional[bool] = True
    role: Optional[str] = "PATIENT"  # Default to PATIENT

    class Config:
        orm_mode = True

class PatientInfoResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    
    class Config:
        orm_mode = True

class UserItemResponse(UserBase):
    user_id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool
    is_first_login: bool
    role: Optional[str] = "PATIENT"  # Default to PATIENT
    patient: Optional[PatientInfoResponse] = None
    # last_login: Optional[datetime] # Removed as it is not in the new model

class UserCreateRequest(UserBase):
    full_name: Optional[str]
    password: str = Field(..., min_length=6, max_length=72)
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.PATIENT


class UserRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class CreatePatientByCaretakerRequest(BaseModel):
    patient_full_name: str = Field(..., description="Patient's full name")
    patient_email: EmailStr = Field(..., description="Patient's email address")
    patient_phone: str = Field(..., description="Patient's phone number")


class UserRegisterV2Request(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    phone: Optional[str] = None


class UserUpdateMeRequest(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]


class UserUpdateRoleRequest(BaseModel):
    role: UserRole
