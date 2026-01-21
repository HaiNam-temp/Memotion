"""
AI Package Usage Example

This example shows how to use the AI package with the 3-layer architecture.
"""

import numpy as np
import cv2
from AI.controller.factory import AIControllerFactory
from AI.controller import Phase1Result, Phase2Result, Phase3Result, Phase4Result


def example_usage():
    """Example of how to use the AI controllers."""

    # Initialize factory
    factory = AIControllerFactory(models_dir="./models")
    if not factory.initialize():
        print("Failed to initialize AI controllers")
        return

    # Get controllers
    phase1 = factory.get_phase1_controller()
    phase2 = factory.get_phase2_controller()
    phase3 = factory.get_phase3_controller()
    phase4 = factory.get_phase4_controller()

    # Simulate camera input (replace with actual camera frame)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Phase 1: Pose Detection
    print("=== PHASE 1: Pose Detection ===")
    result1: Phase1Result = phase1.process_frame(dummy_frame, 0)
    print(f"Pose detected: {result1.pose_detected}")
    print(f"Stable detection: {result1.detection_stable}")

    # Phase 2: Calibration
    print("\n=== PHASE 2: Calibration ===")
    from AI.service import JointType
    phase2.select_joint(JointType.LEFT_SHOULDER)
    phase2.start_calibration()
    result2: Phase2Result = phase2.process_frame(dummy_frame, 1000)
    print(f"Calibration progress: {result2.calibration_progress:.1f}%")

    # Phase 3: Motion Sync (would need actual video engine and sync controller)
    print("\n=== PHASE 3: Motion Sync ===")
    # Note: Phase 3 needs additional setup for video engine and sync controller
    # result3: Phase3Result = phase3.process_frame(dummy_frame, 2000)

    # Phase 4: Scoring & Analysis
    print("\n=== PHASE 4: Scoring & Analysis ===")
    result4: Phase4Result = phase4.process_frame(dummy_frame, 3000)
    print(f"Analysis complete: {result4.analysis_complete}")

    print("\nAI Package initialized successfully!")


if __name__ == "__main__":
    example_usage()