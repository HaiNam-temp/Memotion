"""
AI Controller Factory

Factory class to create and manage AI controllers for each phase.
"""

from typing import Optional
from . import (
    Phase1Controller, Phase2Controller, Phase3Controller, Phase4Controller,
    Phase1Result, Phase2Result, Phase3Result, Phase4Result,
)
from ..service import (
    VisionDetector, DetectorConfig, JointType,
    SafeMaxCalibrator, MotionSyncController, HealthScorer,
    PainDetector, VideoEngine,
)


class AIControllerFactory:
    """Factory for creating AI phase controllers."""

    def __init__(self, models_dir: str = "./models"):
        self.models_dir = models_dir
        self.detector: Optional[VisionDetector] = None
        self.phase1_controller: Optional[Phase1Controller] = None
        self.phase2_controller: Optional[Phase2Controller] = None
        self.phase3_controller: Optional[Phase3Controller] = None
        self.phase4_controller: Optional[Phase4Controller] = None

    def initialize(self) -> bool:
        """Initialize all AI components."""
        try:
            # Initialize detector
            config = DetectorConfig(models_dir=self.models_dir)
            self.detector = VisionDetector(config)

            # Initialize controllers
            from ..service import SafeMaxCalibrator, HealthScorer, PainDetector
            calibrator = SafeMaxCalibrator(duration_ms=5000)
            scorer = HealthScorer()
            pain_detector = PainDetector()

            self.phase1_controller = Phase1Controller(self.detector)
            self.phase2_controller = Phase2Controller(self.detector, calibrator)
            self.phase3_controller = Phase3Controller(
                self.detector, None, scorer, None  # sync_controller and video_engine need to be set per session
            )
            self.phase4_controller = Phase4Controller(scorer, pain_detector)

            return True
        except Exception as e:
            print(f"Failed to initialize AI controllers: {e}")
            return False

    def get_phase1_controller(self) -> Optional[Phase1Controller]:
        """Get Phase 1 controller."""
        return self.phase1_controller

    def get_phase2_controller(self) -> Optional[Phase2Controller]:
        """Get Phase 2 controller."""
        return self.phase2_controller

    def get_phase3_controller(self) -> Optional[Phase3Controller]:
        """Get Phase 3 controller."""
        return self.phase3_controller

    def get_phase4_controller(self) -> Optional[Phase4Controller]:
        """Get Phase 4 controller."""
        return self.phase4_controller

    def set_phase3_components(self, sync_controller: MotionSyncController,
                            video_engine: VideoEngine) -> None:
        """Set Phase 3 specific components."""
        if self.phase3_controller:
            self.phase3_controller.sync_controller = sync_controller
            self.phase3_controller.video_engine = video_engine