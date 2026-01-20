"""
Pose Detection Schemas for MEMOTION Backend.

This module defines Pydantic models for pose detection API requests and responses,
following the standard schema structure defined in PROJECT_STRUCTURE.md.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class PoseDetectionSessionStartRequest(BaseModel):
    """Request model for starting a pose detection session."""

    exercise_type: str = Field(..., description="Type/ID of the exercise to perform")
    duration_minutes: int = Field(default=10, description="Duration of the session in minutes")
    camera_source: int = Field(default=0, description="Camera source (0=back, 1=front)")
    model_complexity: int = Field(default=1, description="MediaPipe model complexity (0-2)")
    stability_threshold: float = Field(default=0.7, description="Stability threshold for phase transition")
    min_measuring_frames: int = Field(default=100, description="Minimum frames to collect in measuring phase")
    auto_phase_transition: bool = Field(default=True, description="Enable automatic phase transitions")
    reference_video_path: Optional[str] = Field(default=None, description="Path to reference video")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session association")

    class Config:
        schema_extra = {
            "example": {
                "exercise_type": "arm_raise_001",
                "duration_minutes": 10,
                "camera_source": 0,
                "model_complexity": 1,
                "stability_threshold": 0.7,
                "min_measuring_frames": 100,
                "auto_phase_transition": True,
                "reference_video_path": "videos/arm_raise_001.mp4",
                "task_id": "task_123"
            }
        }


class PoseDetectionSessionStartResponse(BaseModel):
    """Response model for pose detection session start."""

    session_id: str = Field(..., description="Unique session identifier")
    websocket_url: str = Field(..., description="WebSocket URL for real-time communication")
    reference_video_url: Optional[str] = Field(default=None, description="URL to reference video")
    current_phase: str = Field(..., description="Current phase of the session")
    current_screen: str = Field(..., description="Current screen of the session")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "7e537223-68a3-40c6-bf82-8b428a538d20",
                "websocket_url": "ws://api/pose-detection/session/7e537223-68a3-40c6-bf82-8b428a538d20",
                "reference_video_url": "http://localhost:8000/data/videos/arm_raise_001.mp4",
                "current_phase": "detection"
            }
        }


class PoseDetectionResultsResponse(BaseModel):
    """Response model for pose detection results."""

    overall_score: float = Field(..., description="Overall performance score (0-100)")
    rom_scores: Dict[str, float] = Field(..., description="Range of motion scores by joint")
    stability_scores: Dict[str, float] = Field(..., description="Stability scores by joint")
    flow_scores: Dict[str, float] = Field(..., description="Movement flow scores by joint")
    symmetry_scores: Dict[str, float] = Field(..., description="Symmetry scores by body part")
    fatigue_level: str = Field(..., description="Fatigue level assessment")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    duration: float = Field(..., description="Total session duration in seconds")

    class Config:
        schema_extra = {
            "example": {
                "overall_score": 92.5,
                "rom_scores": {"left_shoulder": 90.0, "right_shoulder": 88.0},
                "stability_scores": {"left_shoulder": 92.0, "right_shoulder": 89.0},
                "flow_scores": {"left_shoulder": 88.0, "right_shoulder": 85.0},
                "symmetry_scores": {"shoulder": 95.0},
                "fatigue_level": "light",
                "recommendations": ["Great job!", "Try to maintain symmetry"],
                "duration": 9.23
            }
        }


class PoseDetectionSessionEndRequest(BaseModel):
    """Request model for ending a pose detection session."""

    task_id: str = Field(..., description="Task ID for validation")

    class Config:
        schema_extra = {
            "example": {
                "task_id": "task_123"
            }
        }


class PoseDetectionSessionEndResponse(BaseModel):
    """Response model for pose detection session end."""

    session_id: str = Field(..., description="Session ID that was ended")
    task_id: str = Field(..., description="Associated task ID")
    completion_score: float = Field(..., description="Final completion score")
    duration_held: float = Field(..., description="Duration the pose was held in seconds")
    results: PoseDetectionResultsResponse = Field(..., description="Complete session results")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "7e537223-68a3-40c6-bf82-8b428a538d20",
                "task_id": "task_123",
                "completion_score": 92.5,
                "duration_held": 9.23,
                "results": {
                    "overall_score": 92.5,
                    "rom_scores": {"left_shoulder": 90.0, "right_shoulder": 88.0},
                    "stability_scores": {"left_shoulder": 92.0, "right_shoulder": 89.0},
                    "flow_scores": {"left_shoulder": 88.0, "right_shoulder": 85.0},
                    "symmetry_scores": {"shoulder": 95.0},
                    "fatigue_level": "light",
                    "recommendations": ["Great job!", "Try to maintain symmetry"],
                    "duration": 9.23
                }
            }
        }


class PoseDetectionHealthResponse(BaseModel):
    """Response model for pose detection service health check."""

    status: str = Field(..., description="Service status")
    mediapipe_available: bool = Field(..., description="MediaPipe availability")
    active_sessions: int = Field(..., description="Number of active sessions")
    version: str = Field(..., description="Service version")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "mediapipe_available": True,
                "active_sessions": 5,
                "version": "1.0.0"
            }
        }