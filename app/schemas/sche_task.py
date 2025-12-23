from typing import Optional
from pydantic import BaseModel
from datetime import date, time
from uuid import UUID

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_date: date
    task_time: time
    task_type: str
    status: str
    owner_type: str

class TaskResponse(TaskBase):
    task_id: UUID
    care_plan_id: UUID
    medication_id: Optional[UUID] = None
    nutrition_id: Optional[UUID] = None
    exercise_id: Optional[UUID] = None
    linked_task_id: Optional[UUID] = None

    class Config:
        orm_mode = True

class MedicationDetail(BaseModel):
    medication_id: UUID
    name: Optional[str]
    description: Optional[str]
    dosage: Optional[str]
    frequency_per_day: Optional[int]
    notes: Optional[str]
    image_path: Optional[str]

    class Config:
        orm_mode = True

class NutritionDetail(BaseModel):
    nutrition_id: UUID
    name: Optional[str]
    calories: Optional[int]
    description: Optional[str]
    meal_type: Optional[str]
    image_path: Optional[str]

    class Config:
        orm_mode = True

class ExerciseDetail(BaseModel):
    exercise_id: UUID
    name: str
    target_body_region: Optional[str]
    description: Optional[str]
    duration_minutes: Optional[int]
    difficulty_level: Optional[int]
    video_path: Optional[str]

    class Config:
        orm_mode = True

class TaskDetailResponse(TaskResponse):
    medication_detail: Optional[MedicationDetail] = None
    nutrition_detail: Optional[NutritionDetail] = None
    exercise_detail: Optional[ExerciseDetail] = None

