"""
Pain Detection Module for MEMOTION.

Detects pain levels based on motion patterns and facial expressions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import numpy as np


class PainLevel(Enum):
    """Pain levels."""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class PainDetector:
    """
    Detects pain from motion patterns and facial expressions.
    """

    # Pain detection parameters
    jerk_threshold: float = 1000.0  # Jerk threshold for pain detection
    asymmetry_threshold: float = 15.0  # Angle asymmetry threshold
    facial_pain_threshold: float = 0.7  # Facial expression threshold

    # State
    pain_history: List[PainLevel] = field(default_factory=list)
    jerk_history: List[float] = field(default_factory=list)
    asymmetry_history: List[float] = field(default_factory=list)

    def detect_pain(self, landmarks: List, face_landmarks: Optional[List] = None) -> PainLevel:
        """
        Detect pain level from current pose and face landmarks.

        Args:
            landmarks: Pose landmarks
            face_landmarks: Face landmarks (optional)

        Returns:
            Detected pain level
        """
        if not landmarks:
            return PainLevel.NONE

        # Calculate motion jerk (simplified)
        jerk = self._calculate_jerk(landmarks)
        self.jerk_history.append(jerk)

        # Keep history limited
        if len(self.jerk_history) > 10:
            self.jerk_history.pop(0)

        # Calculate asymmetry
        asymmetry = self._calculate_asymmetry(landmarks)
        self.asymmetry_history.append(asymmetry)

        if len(self.asymmetry_history) > 10:
            self.asymmetry_history.pop(0)

        # Facial pain detection (placeholder)
        facial_pain = 0.0
        if face_landmarks:
            facial_pain = self._analyze_facial_pain(face_landmarks)

        # Determine pain level
        pain_score = 0.0

        # Jerk contribution
        avg_jerk = np.mean(self.jerk_history) if self.jerk_history else 0.0
        if avg_jerk > self.jerk_threshold * 2:
            pain_score += 0.4
        elif avg_jerk > self.jerk_threshold:
            pain_score += 0.2

        # Asymmetry contribution
        avg_asymmetry = np.mean(self.asymmetry_history) if self.asymmetry_history else 0.0
        if avg_asymmetry > self.asymmetry_threshold * 2:
            pain_score += 0.4
        elif avg_asymmetry > self.asymmetry_threshold:
            pain_score += 0.2

        # Facial contribution
        if facial_pain > self.facial_pain_threshold:
            pain_score += 0.3

        # Determine level
        if pain_score >= 0.7:
            level = PainLevel.SEVERE
        elif pain_score >= 0.4:
            level = PainLevel.MODERATE
        elif pain_score >= 0.2:
            level = PainLevel.MILD
        else:
            level = PainLevel.NONE

        self.pain_history.append(level)
        if len(self.pain_history) > 20:
            self.pain_history.pop(0)

        return level

    def _calculate_jerk(self, landmarks: List) -> float:
        """Calculate motion jerk (simplified)."""
        if len(landmarks) < 2:
            return 0.0

        # Use shoulder movement as proxy
        if len(landmarks) > 12:  # Has shoulder landmarks
            shoulder_y = landmarks[12].y  # Right shoulder Y
            # Simplified jerk calculation
            return abs(shoulder_y * 1000)  # Arbitrary scaling

        return 0.0

    def _calculate_asymmetry(self, landmarks: List) -> float:
        """Calculate left-right asymmetry."""
        if len(landmarks) < 25:  # Need both shoulders and hips
            return 0.0

        # Shoulder asymmetry
        left_shoulder = landmarks[11]   # Left shoulder
        right_shoulder = landmarks[12]  # Right shoulder

        shoulder_diff = abs(left_shoulder.y - right_shoulder.y)

        # Hip asymmetry
        left_hip = landmarks[23]   # Left hip
        right_hip = landmarks[24]  # Right hip

        hip_diff = abs(left_hip.y - right_hip.y)

        return (shoulder_diff + hip_diff) * 100  # Convert to degrees

    def _analyze_facial_pain(self, face_landmarks: List) -> float:
        """Analyze facial expressions for pain (placeholder)."""
        # Placeholder implementation
        # In real implementation, would analyze eye brows, mouth, etc.
        return 0.0