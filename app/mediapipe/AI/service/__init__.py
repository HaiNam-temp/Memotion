"""
Service Layer - Core AI Algorithm Processing

This layer contains all the core AI algorithms copied from the original mediapipe package.
No logic changes - just reorganized for better architecture.
"""

# Import all core AI components
from .detector import (
    VisionDetector, DetectorConfig,
)

from .kinematics import (
    JointType, JOINT_DEFINITIONS, calculate_joint_angle
)

from .synchronizer import (
    MotionPhase, SyncStatus, SyncState, MotionSyncController,
    create_arm_raise_exercise, create_elbow_flex_exercise,
)

from .dtw_analysis import compute_single_joint_dtw
from .data_types import PoseLandmarkIndex

# Import all module components
from .scoring import (
    HealthScorer, FatigueLevel,
    calculate_jerk, calculate_center_of_mass,
)

from .calibration import (
    SafeMaxCalibrator, CalibrationState,
)

from .pain_detection import (
    PainDetector, PainLevel,
)

from .target_generator import (
    rescale_reference_motion,
)

from .video_engine import (
    VideoEngine, PlaybackState,
)

# Re-export all classes and functions for easy access
__all__ = [
    # Core
    'VisionDetector', 'DetectorConfig', 'JointType', 'JOINT_DEFINITIONS',
    'calculate_joint_angle', 'MotionPhase', 'SyncStatus', 'SyncState',
    'MotionSyncController', 'create_arm_raise_exercise', 'create_elbow_flex_exercise',
    'compute_single_joint_dtw', 'PoseLandmarkIndex',

    # Modules
    'HealthScorer', 'FatigueLevel',
    'calculate_jerk', 'calculate_center_of_mass',
    'SafeMaxCalibrator', 'CalibrationState',
    'PainDetector', 'PainLevel',
    'rescale_reference_motion',
    'VideoEngine', 'PlaybackState',
]