"""
Phase 4 Controller - Scoring & Analysis

Controller for Phase 4: Final scoring, fatigue analysis, and pain detection.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

import numpy as np

from ..service import HealthScorer, PainDetector


@dataclass
class Phase4Result:
    """Result from Phase 4 processing."""
    final_score: float = 0.0
    average_score: float = 0.0
    total_reps: int = 0
    fatigue_level: str = "FRESH"
    pain_level: str = "NONE"
    analysis_complete: bool = False
    report: Dict[str, Any] = None


class Phase4Controller:
    """Controller for Phase 4: Scoring & Analysis."""

    def __init__(self, scorer: HealthScorer, pain_detector: PainDetector):
        self.scorer = scorer
        self.pain_detector = pain_detector
        self.analysis_complete = False

    def process_frame(self, camera_frame: np.ndarray, timestamp_ms: int,
                     pose_landmarks: Optional[np.ndarray] = None,
                     face_landmarks: Optional[np.ndarray] = None) -> Phase4Result:
        """
        Process camera frame for final scoring and analysis.

        Args:
            camera_frame: Input frame from user camera
            timestamp_ms: Timestamp in milliseconds
            pose_landmarks: Pose landmarks from detector
            face_landmarks: Face landmarks from detector

        Returns:
            Phase4Result: Final analysis results
        """
        final_score = 0.0
        average_score = 0.0
        total_reps = 0
        fatigue_level = "FRESH"
        pain_level = "NONE"
        report = {}

        # Get scoring results
        if self.scorer.session_active:
            scoring_result = self.scorer.get_final_score()
            final_score = scoring_result.overall_score
            average_score = scoring_result.average_score
            total_reps = scoring_result.total_reps
            fatigue_level = scoring_result.fatigue_level.value

        # Analyze pain if face landmarks available
        if face_landmarks is not None:
            pain_result = self.pain_detector.analyze(face_landmarks)
            if pain_result.is_pain_detected:
                pain_level = pain_result.pain_level.name

        # Generate report
        report = {
            "final_score": final_score,
            "average_score": average_score,
            "total_reps": total_reps,
            "fatigue_level": fatigue_level,
            "pain_level": pain_level,
            "session_duration": self.scorer.get_session_duration() if self.scorer.session_active else 0,
            "timestamp": timestamp_ms
        }

        self.analysis_complete = True

        return Phase4Result(
            final_score=final_score,
            average_score=average_score,
            total_reps=total_reps,
            fatigue_level=fatigue_level,
            pain_level=pain_level,
            analysis_complete=self.analysis_complete,
            report=report
        )