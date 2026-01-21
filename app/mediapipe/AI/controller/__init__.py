"""
Controller Layer - Phase Controllers

This layer contains the 4 main phase controllers that orchestrate AI processing.
Each phase controller calls the appropriate service functions.
"""

# Import phase controllers and results
from .phase1_controller import Phase1Controller, Phase1Result
from .phase2_controller import Phase2Controller, Phase2Result
from .phase3_controller import Phase3Controller, Phase3Result
from .phase4_controller import Phase4Controller, Phase4Result

# Re-export for easy access
__all__ = [
    'Phase1Controller', 'Phase1Result',
    'Phase2Controller', 'Phase2Result',
    'Phase3Controller', 'Phase3Result',
    'Phase4Controller', 'Phase4Result',
]