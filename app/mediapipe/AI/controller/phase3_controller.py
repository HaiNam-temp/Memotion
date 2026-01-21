"""
Phase 3 Controller - Motion Synchronization

Controller for Phase 3: Real-time motion sync with reference video.
"""

import time
from typing import Optional
from dataclasses import dataclass

import numpy as np

from ..service import (
    VisionDetector, JointType, calculate_joint_angle,
    MotionSyncController, SyncState, MotionPhase, SyncStatus,
    HealthScorer, VideoEngine, PlaybackState
)


@dataclass
class Phase3Result:
    """Result from Phase 3 processing."""
    sync_state: Optional[SyncState] = None
    user_angle: float = 0.0
    target_angle: float = 0.0
    motion_phase: str = "idle"
    rep_count: int = 0
    current_score: float = 0.0
    message: str = ""


class Phase3Controller:
    """Controller for Phase 3: Motion Sync."""

    def __init__(self, detector: VisionDetector, sync_controller: MotionSyncController,
                 scorer: HealthScorer, video_engine: VideoEngine):
        self.detector = detector
        self.sync_controller = sync_controller
        self.scorer = scorer
        self.video_engine = video_engine
        self.rep_count = 0
        self.last_phase = MotionPhase.IDLE

    def process_frame(self, camera_frame: np.ndarray, timestamp_ms: int) -> Phase3Result:
        """
        Process camera frame for motion synchronization.

        Args:
            camera_frame: Input frame from user camera
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Phase3Result: Sync results
        """
        result = self.detector.process_frame(camera_frame, timestamp_ms)

        user_angle = 0.0
        target_angle = 0.0
        motion_phase = "idle"
        current_score = 0.0
        message = ""

        if result.has_pose():
            try:
                # Assume default joint for now - can be parameterized
                joint = JointType.LEFT_SHOULDER
                user_angle = calculate_joint_angle(
                    result.pose_landmarks.to_numpy(),
                    joint,
                    use_3d=True
                )

                # Get current frame from video engine
                current_frame = self.video_engine.current_frame
                current_time = time.time()

                # Update sync controller
                sync_state = self.sync_controller.update(user_angle, current_frame, current_time)

                target_angle = sync_state.target_angle
                motion_phase = sync_state.current_phase.value if sync_state.current_phase else "idle"

                # Calculate score
                if target_angle > 0:
                    current_score = self._calculate_realtime_score(user_angle, target_angle)

                # Update scorer
                self.scorer.add_frame(user_angle, current_time, sync_state.current_phase,
                                    pose_landmarks=result.pose_landmarks.to_numpy())

                # Check for rep completion
                if (self.last_phase == MotionPhase.CONCENTRIC and
                    sync_state.current_phase == MotionPhase.IDLE):
                    self.rep_count += 1
                    message = f"Rep {self.rep_count} completed!"

                self.last_phase = sync_state.current_phase

                # Control video playback
                if sync_state.sync_status == SyncStatus.PAUSE:
                    self.video_engine.pause()
                elif sync_state.sync_status in (SyncStatus.PLAY, SyncStatus.SKIP):
                    if self.video_engine.state != PlaybackState.PLAYING:
                        self.video_engine.play()

            except ValueError:
                message = "Unable to calculate joint angle"

        return Phase3Result(
            sync_state=sync_state if 'sync_state' in locals() else None,
            user_angle=user_angle,
            target_angle=target_angle,
            motion_phase=motion_phase,
            rep_count=self.rep_count,
            current_score=current_score,
            message=message
        )

    def _calculate_realtime_score(self, user_angle: float, target_angle: float) -> float:
        """Calculate realtime score between user and target angles."""
        if target_angle == 0:
            return 0.0

        error = abs(user_angle - target_angle)
        max_error = max(target_angle * 0.5, 30.0)  # Allow 50% error or 30 degrees minimum

        score = max(0.0, 100.0 * (1.0 - error / max_error))
        return score