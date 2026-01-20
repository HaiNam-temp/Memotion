"""
Motion Synchronizer Module for MEMOTION.

Handles synchronization between user motion and reference video.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

from .data_types import (
    SyncState, SyncStatus, MotionPhase, Point3D,
    JointType, PoseLandmarkIndex
)
from .kinematics import calculate_angle_from_landmarks, compute_single_joint_dtw


@dataclass
class MotionSyncController:
    """
    Controller for synchronizing user motion with reference exercise.
    """

    reference_angles: List[float] = field(default_factory=list)
    user_angles_history: List[float] = field(default_factory=list)
    sync_state: SyncState = field(default_factory=SyncState)
    joint_type: JointType = JointType.LEFT_SHOULDER
    dtw_window_size: int = 30  # frames
    sync_threshold: float = 15.0  # degrees

    def __post_init__(self):
        if not self.reference_angles:
            self.reference_angles = []

    def update_reference(self, reference_angles: List[float]):
        """Update reference motion data."""
        self.reference_angles = reference_angles.copy()

    def process_frame(self, landmarks: List[Point3D]) -> SyncState:
        """
        Process a frame of user landmarks and update sync state.

        Args:
            landmarks: Current user pose landmarks

        Returns:
            Updated sync state
        """
        if not landmarks or not self.reference_angles:
            self.sync_state.status = SyncStatus.LOST
            return self.sync_state

        # Calculate current user angle
        current_angle = calculate_angle_from_landmarks(landmarks, self.joint_type)
        self.user_angles_history.append(current_angle)

        # Keep only recent history
        if len(self.user_angles_history) > self.dtw_window_size:
            self.user_angles_history.pop(0)

        # Find best sync position
        if len(self.user_angles_history) >= 5:  # Need minimum history
            best_sync_pos, sync_score = self._find_best_sync_position()

            # Update sync state
            self._update_sync_state(best_sync_pos, sync_score)

        return self.sync_state

    def _find_best_sync_position(self) -> Tuple[int, float]:
        """
        Find the best synchronization position in reference motion.

        Returns:
            Tuple of (position, score)
        """
        min_distance = float('inf')
        best_pos = 0

        user_angles = self.user_angles_history

        for i in range(len(self.reference_angles) - len(user_angles) + 1):
            ref_segment = self.reference_angles[i:i+len(user_angles)]
            distance = compute_single_joint_dtw(user_angles, ref_segment)

            if distance < min_distance:
                min_distance = distance
                best_pos = i + len(user_angles) // 2  # Center of segment

        return best_pos, min_distance

    def _update_sync_state(self, sync_pos: int, sync_score: float):
        """Update the synchronization state."""
        # Calculate progress
        progress = sync_pos / len(self.reference_angles) if self.reference_angles else 0.0

        # Determine status
        if sync_score < self.sync_threshold:
            status = SyncStatus.SYNCED
        elif sync_score < self.sync_threshold * 2:
            status = SyncStatus.BEHIND if progress < 0.5 else SyncStatus.AHEAD
        else:
            status = SyncStatus.LOST

        # Determine phase
        if progress < 0.3:
            phase = MotionPhase.PREPARATION
        elif progress < 0.7:
            phase = MotionPhase.EXECUTION
        else:
            phase = MotionPhase.RETURN

        # Get target angle
        target_angle = self.reference_angles[min(sync_pos, len(self.reference_angles)-1)] if self.reference_angles else 0.0

        self.sync_state = SyncState(
            status=status,
            phase=phase,
            progress=progress,
            user_angle=self.user_angles_history[-1] if self.user_angles_history else 0.0,
            target_angle=target_angle,
            sync_score=sync_score
        )


def create_arm_raise_exercise() -> List[float]:
    """
    Create reference motion for arm raise exercise.

    Returns:
        List of angles over time
    """
    # Simple arm raise motion: 0° -> 90° -> 0°
    angles = []

    # Preparation phase (0° for 30 frames)
    angles.extend([0.0] * 30)

    # Raise phase (0° to 90° over 45 frames)
    for i in range(45):
        angle = 90.0 * (i / 44)
        angles.append(angle)

    # Hold phase (90° for 15 frames)
    angles.extend([90.0] * 15)

    # Lower phase (90° to 0° over 45 frames)
    for i in range(45):
        angle = 90.0 * (1 - i / 44)
        angles.append(angle)

    # Return phase (0° for 30 frames)
    angles.extend([0.0] * 30)

    return angles


def create_elbow_flex_exercise() -> List[float]:
    """
    Create reference motion for elbow flexion exercise.

    Returns:
        List of angles over time
    """
    # Elbow flexion: 180° -> 90° -> 180°
    angles = []

    # Preparation phase (180° for 30 frames)
    angles.extend([180.0] * 30)

    # Flex phase (180° to 90° over 45 frames)
    for i in range(45):
        angle = 180.0 - 90.0 * (i / 44)
        angles.append(angle)

    # Hold phase (90° for 15 frames)
    angles.extend([90.0] * 15)

    # Extend phase (90° to 180° over 45 frames)
    for i in range(45):
        angle = 90.0 + 90.0 * (i / 44)
        angles.append(angle)

    # Return phase (180° for 30 frames)
    angles.extend([180.0] * 30)

    return angles