"""
User Profile Module for MEMOTION.

Manages user-specific calibration data and exercise preferences.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import json
import time

from ..core.data_types import JointType


@dataclass
class UserProfile:
    """
    User profile with calibration data and preferences.
    """

    user_id: str
    name: str = ""

    # Calibration data
    safe_max_angles: Dict[str, float] = field(default_factory=dict)

    # Exercise preferences
    preferred_joints: List[JointType] = field(default_factory=lambda: [JointType.LEFT_SHOULDER])
    exercise_history: List[Dict] = field(default_factory=list)

    # Profile metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def set_safe_max_angle(self, joint_type: JointType, angle: float):
        """
        Set safe maximum angle for a joint.

        Args:
            joint_type: Type of joint
            angle: Safe maximum angle in degrees
        """
        self.safe_max_angles[joint_type.value] = angle
        self.updated_at = time.time()

    def get_safe_max_angle(self, joint_type: JointType) -> float:
        """
        Get safe maximum angle for a joint.

        Args:
            joint_type: Type of joint

        Returns:
            Safe maximum angle, or 90.0 if not calibrated
        """
        return self.safe_max_angles.get(joint_type.value, 90.0)

    def add_exercise_session(self, exercise_data: Dict):
        """
        Add exercise session to history.

        Args:
            exercise_data: Exercise session data
        """
        session = {
            'timestamp': time.time(),
            **exercise_data
        }
        self.exercise_history.append(session)

        # Keep only last 50 sessions
        if len(self.exercise_history) > 50:
            self.exercise_history = self.exercise_history[-50:]

        self.updated_at = time.time()

    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent exercise sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of recent sessions
        """
        return self.exercise_history[-limit:]

    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'safe_max_angles': self.safe_max_angles,
            'preferred_joints': [jt.value for jt in self.preferred_joints],
            'exercise_history': self.exercise_history,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        """Create profile from dictionary."""
        profile = cls(
            user_id=data['user_id'],
            name=data.get('name', ''),
            safe_max_angles=data.get('safe_max_angles', {}),
            exercise_history=data.get('exercise_history', [])
        )

        # Convert joint types
        preferred_joints = []
        for jt_str in data.get('preferred_joints', []):
            try:
                jt = JointType(jt_str)
                preferred_joints.append(jt)
            except ValueError:
                pass
        profile.preferred_joints = preferred_joints or [JointType.LEFT_SHOULDER]

        profile.created_at = data.get('created_at', time.time())
        profile.updated_at = data.get('updated_at', time.time())

        return profile

    def save_to_file(self, file_path: str):
        """Save profile to JSON file."""
        data = self.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['UserProfile']:
        """Load profile from JSON file."""
        if not Path(file_path).exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None