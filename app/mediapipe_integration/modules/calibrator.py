"""
Calibration Module for MEMOTION.

Handles safe maximum angle calibration for users.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import time

from ..core.data_types import JointType, Point3D
from ..core.kinematics import calculate_angle_from_landmarks


class CalibrationState(Enum):
    """Calibration states."""
    IDLE = "idle"
    MEASURING = "measuring"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SafeMaxCalibrator:
    """
    Calibrates safe maximum motion angles for users.
    """

    joint_type: JointType = JointType.LEFT_SHOULDER
    state: CalibrationState = CalibrationState.IDLE

    # Calibration parameters
    measurement_duration: int = 10  # seconds
    safety_margin: float = 0.9  # 90% of max measured

    # Data collection
    angle_measurements: List[float] = field(default_factory=list)
    start_time: Optional[float] = None
    max_angle: float = 0.0
    safe_max_angle: float = 0.0

    def start_calibration(self):
        """Start the calibration process."""
        self.state = CalibrationState.MEASURING
        self.angle_measurements = []
        self.max_angle = 0.0
        self.safe_max_angle = 0.0
        self.start_time = time.time()

    def update_calibration(self, landmarks: List[Point3D]) -> bool:
        """
        Update calibration with new landmarks.

        Args:
            landmarks: Current pose landmarks

        Returns:
            True if calibration completed
        """
        if self.state != CalibrationState.MEASURING:
            return False

        if not self.start_time:
            return False

        # Check timeout
        elapsed = time.time() - self.start_time
        if elapsed >= self.measurement_duration:
            self._complete_calibration()
            return True

        # Measure angle
        current_angle = calculate_angle_from_landmarks(landmarks, self.joint_type)
        if current_angle > 0:
            self.angle_measurements.append(current_angle)
            self.max_angle = max(self.max_angle, current_angle)

        return False

    def _complete_calibration(self):
        """Complete the calibration process."""
        if not self.angle_measurements:
            self.state = CalibrationState.FAILED
            return

        # Calculate safe max (with margin)
        self.safe_max_angle = self.max_angle * self.safety_margin

        # Ensure minimum angle
        self.safe_max_angle = max(self.safe_max_angle, 30.0)  # Minimum 30 degrees

        self.state = CalibrationState.COMPLETED

    def get_calibration_result(self) -> Dict:
        """
        Get calibration results.

        Returns:
            Dictionary with calibration data
        """
        return {
            'joint_type': self.joint_type.value,
            'max_angle': self.max_angle,
            'safe_max_angle': self.safe_max_angle,
            'measurements': len(self.angle_measurements),
            'state': self.state.value
        }

    def reset(self):
        """Reset calibration."""
        self.state = CalibrationState.IDLE
        self.angle_measurements = []
        self.start_time = None
        self.max_angle = 0.0
        self.safe_max_angle = 0.0