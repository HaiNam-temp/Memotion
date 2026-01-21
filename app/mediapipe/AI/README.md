# AI Package Structure
```
AI/
├── __init__.py              # Package initialization
├── data/                    # Data access layer
│   └── __init__.py         # Database queries and persistence
├── service/                 # Core AI algorithms
│   ├── __init__.py         # Service layer imports
│   ├── detector.py         # Pose detection (copied from core/)
│   ├── synchronizer.py     # Motion sync (copied from core/)
│   ├── dtw_analysis.py     # DTW analysis (copied from core/)
│   ├── kinematics.py       # Joint calculations (copied from core/)
│   ├── procrustes.py       # Procrustes analysis (copied from core/)
│   ├── scoring.py          # Health scoring (copied from modules/)
│   ├── calibration.py      # Safe-max calibration (copied from modules/)
│   ├── pain_detection.py   # Pain detection (copied from modules/)
│   ├── target_generator.py # Exercise generation (copied from modules/)
│   └── video_engine.py     # Video playback (copied from modules/)
├── controller/              # Phase controllers
│   ├── __init__.py         # Phase controllers and result classes
│   └── factory.py          # Controller factory
└── example.py              # Usage example
```

## Architecture Overview

### 1. Data Layer (`data/`)
- Handles database queries and data persistence
- Minimal implementation as most processing is real-time
- Functions: save/load session logs, user profiles

### 2. Service Layer (`service/`)
- Contains all core AI algorithms (copied unchanged from original mediapipe package)
- No logic modifications - pure refactoring for organization
- Includes: pose detection, motion sync, scoring, calibration, pain detection

### 3. Controller Layer (`controller/`)
- 4 main phase controllers: Phase1Controller, Phase2Controller, Phase3Controller, Phase4Controller
- Each controller orchestrates AI processing for its phase
- Input: camera frames, Output: structured results (PhaseXResult dataclasses)
- Factory pattern for easy initialization and management

## Usage

```python
from AI.controller.factory import AIControllerFactory

# Initialize
factory = AIControllerFactory()
factory.initialize()

# Get controllers
phase1 = factory.get_phase1_controller()

# Process frames
result = phase1.process_frame(camera_frame, timestamp_ms)
```

## Integration with Backend

The controller layer is designed for easy backend integration:
- Clean input/output interfaces
- No UI dependencies
- Structured result objects
- Factory pattern for dependency injection