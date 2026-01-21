"""
Phase 1 Controller - Pose Detection

Controller for Phase 1: Pose Detection and stability checking.
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

from ..service import VisionDetector, JointType, calculate_joint_angle


@dataclass
class Phase1Result:
    """Result from Phase 1 processing."""
    pose_detected: bool = False
    landmarks: Optional[np.ndarray] = None
    joint_angles: Dict[JointType, float] = None
    detection_stable: bool = False
    message: str = ""


class Phase1Controller:
    """Controller for Phase 1: Pose Detection."""

    def __init__(self, detector: VisionDetector):
        self.detector = detector
        self.stable_count = 0
        self.detection_threshold = 30  # frames

    def process_frame(self, camera_frame: np.ndarray, timestamp_ms: int) -> Phase1Result:
        """
        Process camera frame for pose detection.

        Args:
            camera_frame: Input frame from user camera
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Phase1Result: Detection results
        """
        result = self.detector.process_frame(camera_frame, timestamp_ms)

        pose_detected = result.has_pose()
        landmarks = None
        joint_angles = {}

        if pose_detected:
            landmarks = result.pose_landmarks.to_numpy()

            # Calculate angles for key joints
            for joint in [JointType.LEFT_SHOULDER, JointType.RIGHT_SHOULDER,
                         JointType.LEFT_ELBOW, JointType.RIGHT_ELBOW,
                         JointType.LEFT_KNEE, JointType.RIGHT_KNEE]:
                try:
                    angle = calculate_joint_angle(landmarks, joint, use_3d=True)
                    joint_angles[joint] = angle
                except ValueError:
                    joint_angles[joint] = 0.0

            self.stable_count += 1
        else:
            self.stable_count = 0

        detection_stable = self.stable_count >= self.detection_threshold

        message = "Pose detected and stable" if detection_stable else "Detecting pose..."

        return Phase1Result(
            pose_detected=pose_detected,
            landmarks=landmarks,
            joint_angles=joint_angles,
            detection_stable=detection_stable,
            message=message
        )