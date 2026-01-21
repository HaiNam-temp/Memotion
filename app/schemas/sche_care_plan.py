"""
Schemas for AI Care Plan Agent.
Request/Response models for care plan generation and task refinement.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CarePlanGenerationRequest(BaseModel):
    """Request schema for AI care plan generation."""
    plan_duration_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Duration of care plan in days (1-30)"
    )
    regenerate: bool = Field(
        default=False,
        description="Force regenerate even if plan exists"
    )
    
    class Config:
        extra = "ignore"  # Allow extra fields to be ignored
        json_schema_extra = {
            "example": {
                "plan_duration_days": 7,
                "regenerate": False
            }
        }


class TaskRecommendation(BaseModel):
    """AI-generated task recommendation."""
    owner_type: str = Field(..., description="PATIENT or CARETAKER")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    task_type: str = Field(..., description="MEDICATION, NUTRITION, or EXERCISE")
    schedule_time: str = Field(..., description="Scheduled time (HH:MM)")
    priority: str = Field(..., description="HIGH, MEDIUM, or LOW")
    resource_id: Optional[str] = Field(None, description="UUID of medication/nutrition/exercise")
    notes: Optional[str] = Field(None, description="Additional notes")


class AICarePlanResponse(BaseModel):
    """Response from AI agent containing care plan."""
    tasks: List[TaskRecommendation] = Field(..., description="List of recommended tasks")
    recommendations: List[str] = Field(default_factory=list, description="General care recommendations")
    plan_duration_days: int = Field(..., description="Plan duration")
    generated_at: str = Field(..., description="Generation timestamp (ISO format)")


class CarePlanSummaryResponse(BaseModel):
    """Summary of care plan with statistics."""
    care_plan_id: str = Field(..., description="Care plan UUID")
    patient_id: str = Field(..., description="Patient UUID")
    caretaker_id: str = Field(..., description="Caretaker UUID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    task_statistics: Dict[str, Any] = Field(..., description="Task stats by type and status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "care_plan_id": "123e4567-e89b-12d3-a456-426614174000",
                "patient_id": "123e4567-e89b-12d3-a456-426614174001",
                "caretaker_id": "123e4567-e89b-12d3-a456-426614174002",
                "created_at": "2026-01-07T10:30:00",
                "updated_at": "2026-01-07T10:30:00",
                "task_statistics": {
                    "total": 28,
                    "pending": 20,
                    "done": 8,
                    "by_type": {
                        "MEDICATION": 12,
                        "NUTRITION": 8,
                        "EXERCISE": 5,
                        "GENERAL": 3
                    }
                }
            }
        }


class CarePlanUpdateResponse(BaseModel):
    """Response after successful care plan update."""
    care_plan_id: str = Field(..., description="Updated care plan UUID")
    patient_id: str = Field(..., description="Patient UUID")
    caretaker_id: str = Field(..., description="Caretaker UUID")
    plan_duration_days: int = Field(..., description="Plan duration in days")
    total_tasks: int = Field(..., description="Total tasks after update")
    tasks_updated: int = Field(..., description="Tasks updated")
    recommendations: List[str] = Field(default_factory=list, description="AI recommendations")
    updated_at: str = Field(..., description="Update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "care_plan_id": "123e4567-e89b-12d3-a456-426614174000",
                "patient_id": "123e4567-e89b-12d3-a456-426614174001",
                "caretaker_id": "123e4567-e89b-12d3-a456-426614174002",
                "plan_duration_days": 7,
                "total_tasks": 28,
                "tasks_updated": 28,
                "recommendations": [
                    "Monitor pain levels daily",
                    "Encourage hydration",
                    "Schedule physical therapy follow-up"
                ],
                "updated_at": "2026-01-07T10:30:00"
            }
        }


class CarePlanGenerationResponse(BaseModel):
    """Response after successful care plan generation."""
    care_plan_id: str = Field(..., description="Created care plan UUID")
    patient_id: str = Field(..., description="Patient UUID")
    caretaker_id: str = Field(..., description="Caretaker UUID")
    plan_duration_days: int = Field(..., description="Plan duration in days")
    total_tasks: int = Field(..., description="Total tasks created")
    tasks_created: int = Field(..., description="Successfully created tasks")
    recommendations: List[str] = Field(default_factory=list, description="AI recommendations")
    generated_at: str = Field(..., description="Generation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "care_plan_id": "123e4567-e89b-12d3-a456-426614174000",
                "patient_id": "123e4567-e89b-12d3-a456-426614174001",
                "caretaker_id": "123e4567-e89b-12d3-a456-426614174002",
                "plan_duration_days": 7,
                "total_tasks": 28,
                "tasks_created": 28,
                "recommendations": [
                    "Monitor pain levels daily",
                    "Encourage hydration",
                    "Schedule physical therapy follow-up"
                ],
                "generated_at": "2026-01-07T10:30:00"
            }
        }


class CarePlanDeletionResponse(BaseModel):
    """Response after successful care plan deletion."""
    message: str = Field(..., description="Success message")
    patient_id: str = Field(..., description="Patient UUID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Care plan deleted successfully",
                "patient_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }


class TaskRefinementRequest(BaseModel):
    """Request to refine a task using AI."""
    patient_feedback: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Patient's feedback about the task"
    )
    
    class Config:
        extra = "ignore"  # Allow extra fields to be ignored
        json_schema_extra = {
            "example": {
                "patient_feedback": "This exercise is too difficult for me. Can we have something gentler for my knees?"
            }
        }


class TaskRefinementResponse(BaseModel):
    """Response after task refinement."""
    task_id: str = Field(..., description="Task UUID")
    title: str = Field(..., description="Refined task title")
    description: str = Field(..., description="Refined task description")
    refined_at: str = Field(..., description="Refinement timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174010",
                "title": "Gentle Knee Stretching (Modified)",
                "description": "Perform seated gentle knee flexion exercises. Very light movements, focus on comfort not range.",
                "refined_at": "2026-01-07T14:30:00"
            }
        }


class LibraryItemBase(BaseModel):
    """Base schema for library items (medication, nutrition, exercise)."""
    id: str = Field(..., description="Item UUID")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")


class MedicationLibraryItem(LibraryItemBase):
    """Medication library item for AI input."""
    dosage: Optional[str] = Field(None, description="Medication dosage")
    frequency_per_day: Optional[int] = Field(None, description="Times per day")
    notes: Optional[str] = Field(None, description="Additional notes")


class NutritionLibraryItem(LibraryItemBase):
    """Nutrition library item for AI input."""
    calories: Optional[int] = Field(None, description="Calories")
    meal_type: Optional[str] = Field(None, description="BREAKFAST, LUNCH, DINNER, SNACK")


class ExerciseLibraryItem(LibraryItemBase):
    """Exercise library item for AI input."""
    target_body_region: Optional[str] = Field(None, description="Target body part")
    duration_minutes: Optional[int] = Field(None, description="Exercise duration")
    difficulty_level: Optional[int] = Field(None, description="Difficulty (1-5)")


class PatientProfileForAI(BaseModel):
    """Patient profile formatted for AI agent."""
    profile_id: str
    patient_id: str
    gender: Optional[str] = None
    living_arrangement: Optional[str] = None
    bmi_score: Optional[int] = None
    map_score: Optional[int] = None
    rhr_score: Optional[int] = None
    adl_score: Optional[int] = None
    iadl_score: Optional[int] = None
    blood_glucose_level: Optional[int] = None
    disease_type: str
    condition_note: Optional[str] = None
    therapy_detail: Optional[Dict[str, Any]] = None


class AIAgentHealthCheck(BaseModel):
    """Health check response for AI agent."""
    agent_status: str = Field(..., description="Status of AI agent")
    gemini_api_configured: bool = Field(..., description="Whether Gemini API key is set")
    prompt_template_loaded: bool = Field(..., description="Whether prompt template is loaded")
    last_generation: Optional[str] = Field(None, description="Last successful generation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_status": "operational",
                "gemini_api_configured": True,
                "prompt_template_loaded": True,
                "last_generation": "2026-01-07T10:30:00"
            }
        }
