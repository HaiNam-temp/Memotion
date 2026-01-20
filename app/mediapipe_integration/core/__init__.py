"""
Core Module for MEMOTION MediaPipe Integration.

Contains core functionality for pose detection, kinematics, and synchronization.
"""

from .detector import VisionDetector, DetectorConfig
from .data_types import (
    Point3D, LandmarkSet, LandmarkType, DetectionResult,
    JointType, JOINT_DEFINITIONS, MotionPhase, SyncStatus, SyncState,
    NormalizedSkeleton, ProcrustesResult, PoseLandmarkIndex
)
from .kinematics import (
    calculate_joint_angle, calculate_angle_from_landmarks, compute_single_joint_dtw,
    normalize_skeleton, procrustes_analysis
)
from .synchronizer import (
    MotionSyncController, create_arm_raise_exercise, create_elbow_flex_exercise
)

__all__ = [
    # Detector
    'VisionDetector', 'DetectorConfig',

    # Data types
    'Point3D', 'LandmarkSet', 'LandmarkType', 'DetectionResult',
    'JointType', 'JOINT_DEFINITIONS', 'MotionPhase', 'SyncStatus', 'SyncState',
    'NormalizedSkeleton', 'ProcrustesResult', 'PoseLandmarkIndex',

    # Kinematics
    'calculate_joint_angle', 'calculate_angle_from_landmarks', 'compute_single_joint_dtw',
    'normalize_skeleton', 'procrustes_analysis',

    # Synchronizer
    'MotionSyncController', 'create_arm_raise_exercise', 'create_elbow_flex_exercise',
]