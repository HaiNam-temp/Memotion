"""
Data Types Module for MEMOTION MediaPipe Integration.

Contains all data classes, enums, and type definitions used across the system.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import numpy as np


@dataclass
class Point3D:
    """3D point with x, y, z coordinates."""
    x: float
    y: float
    z: float
    visibility: Optional[float] = None
    presence: Optional[float] = None


class LandmarkType(Enum):
    """Types of landmarks."""
    POSE = "pose"
    FACE = "face"
    HAND = "hand"


@dataclass
class LandmarkSet:
    """Set of landmarks for a specific type."""
    landmarks: List[Point3D] = field(default_factory=list)
    landmark_type: LandmarkType = LandmarkType.POSE
    visibility: List[float] = field(default_factory=list)


@dataclass
class DetectionResult:
    """Result of pose/face detection."""
    pose_landmarks: Optional[Any] = None  # Raw Mediapipe NormalizedLandmarkList
    pose_world_landmarks: Optional[Any] = None  # Raw Mediapipe NormalizedLandmarkList
    face_landmarks: Optional[Any] = None  # Raw Mediapipe NormalizedLandmarkList
    timestamp_ms: int = 0


class JointType(Enum):
    """Joint types for angle calculation."""
    LEFT_SHOULDER = "left_shoulder"
    RIGHT_SHOULDER = "right_shoulder"
    LEFT_ELBOW = "left_elbow"
    RIGHT_ELBOW = "right_elbow"
    LEFT_KNEE = "left_knee"
    RIGHT_KNEE = "right_knee"
    LEFT_HIP = "left_hip"
    RIGHT_HIP = "right_hip"


# Joint definitions for angle calculation
JOINT_DEFINITIONS = {
    JointType.LEFT_SHOULDER: {
        'joints': [11, 13, 15],  # shoulder, elbow, wrist
        'description': 'Left shoulder angle'
    },
    JointType.RIGHT_SHOULDER: {
        'joints': [12, 14, 16],  # shoulder, elbow, wrist
        'description': 'Right shoulder angle'
    },
    JointType.LEFT_ELBOW: {
        'joints': [13, 11, 23],  # elbow, shoulder, hip
        'description': 'Left elbow angle'
    },
    JointType.RIGHT_ELBOW: {
        'joints': [14, 12, 24],  # elbow, shoulder, hip
        'description': 'Right elbow angle'
    },
    JointType.LEFT_KNEE: {
        'joints': [23, 25, 27],  # hip, knee, ankle
        'description': 'Left knee angle'
    },
    JointType.RIGHT_KNEE: {
        'joints': [24, 26, 28],  # hip, knee, ankle
        'description': 'Right knee angle'
    },
}


class MotionPhase(Enum):
    """Phases of motion."""
    PREPARATION = "preparation"
    EXECUTION = "execution"
    RETURN = "return"


class SyncStatus(Enum):
    """Synchronization status."""
    SYNCED = "synced"
    BEHIND = "behind"
    AHEAD = "ahead"
    LOST = "lost"


@dataclass
class SyncState:
    """State of motion synchronization."""
    status: SyncStatus = SyncStatus.LOST
    phase: MotionPhase = MotionPhase.PREPARATION
    progress: float = 0.0
    user_angle: float = 0.0
    target_angle: float = 0.0
    sync_score: float = 0.0


@dataclass
class NormalizedSkeleton:
    """Normalized skeleton data."""
    landmarks: List[Point3D] = field(default_factory=list)
    center: Point3D = field(default_factory=lambda: Point3D(0, 0, 0))
    scale: float = 1.0


@dataclass
class ProcrustesResult:
    """Result of Procrustes analysis."""
    rotation_matrix: np.ndarray = field(default_factory=lambda: np.eye(3))
    translation: np.ndarray = field(default_factory=lambda: np.zeros(3))
    scale: float = 1.0
    disparity: float = 0.0


class PoseLandmarkIndex:
    """MediaPipe Pose landmark indices."""
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32