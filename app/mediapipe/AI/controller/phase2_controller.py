"""
Phase 2 Controller - Safe-Max Calibration

Controller for Phase 2: Joint selection and safe-max angle calibration.
"""

from typing import Optional
from dataclasses import dataclass

import numpy as np

from ..service import VisionDetector, JointType, calculate_joint_angle, SafeMaxCalibrator


@dataclass
class Phase2Result:
    """Result from Phase 2 processing."""
    calibration_complete: bool = False
    selected_joint: Optional[JointType] = None
    user_max_angle: float = 0.0
    calibration_progress: float = 0.0
    message: str = ""


class Phase2Controller:
    """Controller for Phase 2: Safe-Max Calibration."""

    def __init__(self, detector: VisionDetector, calibrator: SafeMaxCalibrator):
        self.detector = detector
        self.calibrator = calibrator
        self.selected_joint: Optional[JointType] = None

    def select_joint(self, joint: JointType) -> None:
        """Select joint for calibration."""
        self.selected_joint = joint

    def start_calibration(self) -> None:
        """Start calibration process."""
        if self.selected_joint:
            self.calibrator.start_calibration()

    def process_frame(self, camera_frame: np.ndarray, timestamp_ms: int) -> Phase2Result:
        """
        Process camera frame during calibration.

        Args:
            camera_frame: Input frame from user camera
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Phase2Result: Calibration results
        """
        result = self.detector.process_frame(camera_frame, timestamp_ms)

        user_max_angle = 0.0
        calibration_complete = False
        progress = 0.0
        message = "Select a joint to calibrate"

        if self.selected_joint and result.has_pose():
            try:
                current_angle = calculate_joint_angle(
                    result.pose_landmarks.to_numpy(),
                    self.selected_joint,
                    use_3d=True
                )

                # Update calibrator
                self.calibrator.update_angle(current_angle, timestamp_ms)

                if self.calibrator.is_calibrating:
                    progress = self.calibrator.get_progress()
                    message = f"Calibrating {self.selected_joint.name}: {progress:.1f}%"
                elif self.calibrator.is_complete:
                    user_max_angle = self.calibrator.get_max_angle()
                    calibration_complete = True
                    message = f"Calibration complete! Max angle: {user_max_angle:.1f}°"

            except ValueError:
                message = "Unable to calculate joint angle"

        return Phase2Result(
            calibration_complete=calibration_complete,
            selected_joint=self.selected_joint,
            user_max_angle=user_max_angle,
            calibration_progress=progress,
            message=message
        )