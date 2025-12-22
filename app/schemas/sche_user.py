from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.helpers.enums import UserRole


class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True

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
    role: str
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
    phone: Optional[str] = None
    role: UserRole = UserRole.PATIENT
    
    # Fields for Patient creation if role is CARETAKER
    patient_full_name: Optional[str] = None
    patient_email: Optional[EmailStr] = None
    patient_phone: Optional[str] = None


class UserUpdateMeRequest(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]


class UserUpdateRequest(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    is_active: Optional[bool] = True
    role: Optional[UserRole]
