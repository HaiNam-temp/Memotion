"""
Modules Package for MEMOTION MediaPipe Integration.

Contains specialized modules for video processing, pain detection, scoring, etc.
"""

from .video_engine import VideoEngine, PlaybackState
from .pain_detector import PainDetector, PainLevel
from .health_scorer import HealthScorer, FatigueLevel
from .calibrator import SafeMaxCalibrator, CalibrationState
from .user_profile import UserProfile

# Import from scoring.py if needed
try:
    from .scoring import RepScore, SessionReport
    _has_scoring = True
except ImportError:
    _has_scoring = False

__all__ = [
    # Video Engine
    'VideoEngine', 'PlaybackState',

    # Pain Detection
    'PainDetector', 'PainLevel',

    # Health Scoring
    'HealthScorer', 'FatigueLevel',

    # Calibration
    'SafeMaxCalibrator', 'CalibrationState',

    # User Profile
    'UserProfile',
]

if _has_scoring:
    __all__.extend(['RepScore', 'SessionReport'])