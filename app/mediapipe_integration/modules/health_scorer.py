"""
Health Scorer Module for MEMOTION.

Comprehensive scoring system for exercise quality assessment.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np

from ..core.data_types import JointType, MotionPhase
from .pain_detector import PainLevel


class FatigueLevel(Enum):
    """Fatigue levels."""
    FRESH = "fresh"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


@dataclass
class HealthScorer:
    """
    Comprehensive health scoring system.
    """

    # Scoring weights
    rom_weight: float = 0.3
    stability_weight: float = 0.25
    flow_weight: float = 0.25
    symmetry_weight: float = 0.2

    # Thresholds
    min_rom_score: float = 60.0
    jerk_threshold: float = 500.0

    def calculate_overall_score(self,
                              rom_score: float,
                              stability_score: float,
                              flow_score: float,
                              symmetry_score: float) -> float:
        """
        Calculate overall exercise score.

        Args:
            rom_score: Range of motion score (0-100)
            stability_score: Stability score (0-100)
            flow_score: Motion flow score (0-100)
            symmetry_score: Symmetry score (0-100)

        Returns:
            Overall score (0-100)
        """
        return (rom_score * self.rom_weight +
                stability_score * self.stability_weight +
                flow_score * self.flow_weight +
                symmetry_score * self.symmetry_weight)

    def assess_fatigue(self, jerk_values: List[float], rep_count: int) -> FatigueLevel:
        """
        Assess fatigue level from motion jerk.

        Args:
            jerk_values: List of jerk values over time
            rep_count: Current repetition count

        Returns:
            Fatigue level
        """
        if not jerk_values:
            return FatigueLevel.FRESH

        avg_jerk = np.mean(jerk_values)
        jerk_trend = self._calculate_jerk_trend(jerk_values)

        # Fatigue assessment
        fatigue_score = 0.0

        if avg_jerk > self.jerk_threshold * 2:
            fatigue_score += 0.5
        elif avg_jerk > self.jerk_threshold:
            fatigue_score += 0.3

        if jerk_trend > 0.1:  # Increasing jerk
            fatigue_score += 0.3

        if rep_count > 20:  # High rep count
            fatigue_score += 0.2

        if fatigue_score >= 0.8:
            return FatigueLevel.HEAVY
        elif fatigue_score >= 0.5:
            return FatigueLevel.MODERATE
        elif fatigue_score >= 0.2:
            return FatigueLevel.LIGHT
        else:
            return FatigueLevel.FRESH

    def _calculate_jerk_trend(self, jerk_values: List[float]) -> float:
        """Calculate trend in jerk values."""
        if len(jerk_values) < 5:
            return 0.0

        # Simple linear trend
        x = np.arange(len(jerk_values))
        y = np.array(jerk_values)

        slope = np.polyfit(x, y, 1)[0]
        return slope

    def calculate_symmetry_score(self, left_angles: List[float], right_angles: List[float]) -> float:
        """
        Calculate symmetry score between left and right sides.

        Args:
            left_angles: Left side angles
            right_angles: Right side angles

        Returns:
            Symmetry score (0-100)
        """
        if not left_angles or not right_angles:
            return 50.0

        min_len = min(len(left_angles), len(right_angles))
        left = left_angles[:min_len]
        right = right_angles[:min_len]

        # Calculate asymmetry
        asymmetries = [abs(l - r) for l, r in zip(left, right)]
        avg_asymmetry = np.mean(asymmetries)

        # Convert to score (lower asymmetry = higher score)
        if avg_asymmetry <= 5.0:
            return 100.0
        elif avg_asymmetry <= 15.0:
            return 80.0
        elif avg_asymmetry <= 30.0:
            return 60.0
        else:
            return max(0.0, 100.0 - avg_asymmetry)