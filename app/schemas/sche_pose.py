"""
Pose Detection Schemas - Data Transfer Objects (Simplified).

Real-time WebSocket only - minimal schemas for session management.

Author: MEMOTION Team
Version: 3.0.0
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from enum import Enum


# ==================== ENUMS ====================

class PosePhase(str, Enum):
    """Pose detection phases."""
    DETECTION = "detection"
    CALIBRATION = "calibration"
    SYNC = "sync"
    SCORING = "scoring"
    COMPLETED = "completed"


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


# ==================== REQUEST SCHEMAS ====================

class StartSessionRequest(BaseModel):
    """Request to start a new pose detection session."""
    user_id: Optional[str] = Field(None, description="User identifier")
    exercise_type: Optional[str] = Field("arm_raise", description="Exercise type")
    ref_video_path: Optional[str] = Field(None, description="Reference video path")
    default_joint: str = Field("left_shoulder", description="Default calibration joint")


class ProcessFrameRequest(BaseModel):
    """Request to process a single video frame (used internally by WebSocket)."""
    session_id: str = Field(..., description="Session identifier")
    frame_data: str = Field(..., description="Base64 encoded frame")
    timestamp_ms: int = Field(..., description="Frame timestamp in milliseconds")


# ==================== RESPONSE SCHEMAS ====================

class StartSessionResponse(BaseModel):
    """Response after starting a new session."""
    session_id: str = Field(..., description="Unique session identifier")
    status: SessionStatus = Field(..., description="Session status")
    current_phase: PosePhase = Field(default=PosePhase.DETECTION, description="Current phase")
    websocket_url: str = Field(..., description="WebSocket URL for real-time streaming")
    message: str = Field(..., description="Status message")


class ProcessFrameResponse(BaseModel):
    """Response after processing a frame (sent via WebSocket)."""
    session_id: str = Field(..., description="Session identifier")
    phase: int = Field(..., description="Current phase (1-4)")
    phase_name: str = Field(..., description="Phase name")
    data: Dict[str, Any] = Field(default_factory=dict, description="Phase-specific data")
    message: Optional[str] = Field(None, description="Status message")
    warning: Optional[str] = Field(None, description="Warning message")
    timestamp: float = Field(..., description="Processing timestamp")


class SessionResultsResponse(BaseModel):
    """Response for final session results."""
    session_id: str
    exercise_name: str = ""
    duration_seconds: int = 0
    total_score: float = 0.0
    rom_score: float = 0.0
    stability_score: float = 0.0
    flow_score: float = 0.0
    grade: str = ""
    grade_color: str = "yellow"
    total_reps: int = 0
    fatigue_level: str = "FRESH"
    calibrated_joints: List[Dict[str, Any]] = Field(default_factory=list)
    rep_scores: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class PoseHealthResponse(BaseModel):
    """Response for pose service health check."""
    status: str = Field(..., description="Service status")
    mediapipe_available: bool = Field(..., description="MediaPipe availability")
    active_sessions: int = Field(..., description="Active sessions count")
    version: str = Field(..., description="Service version")
