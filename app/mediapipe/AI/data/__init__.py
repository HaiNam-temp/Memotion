"""
Data Access Layer

Handles database queries and data persistence for AI processing.
Currently minimal as most processing is real-time.
"""

from typing import Dict, List, Optional
import json
import os
from pathlib import Path


class DataAccess:
    """Data access layer for AI processing data."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.logs_dir = self.data_dir / "logs"
        self.user_profiles_dir = self.data_dir / "user_profiles"

    def save_session_log(self, session_id: str, data: Dict) -> bool:
        """Save session log data."""
        try:
            log_file = self.logs_dir / f"{session_id}.json"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving session log: {e}")
            return False

    def load_session_log(self, session_id: str) -> Optional[Dict]:
        """Load session log data."""
        try:
            log_file = self.logs_dir / f"{session_id}.json"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading session log: {e}")
            return None

    def save_user_profile(self, user_id: str, profile: Dict) -> bool:
        """Save user profile data."""
        try:
            profile_file = self.user_profiles_dir / f"user_{user_id}.json"
            profile_file.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False

    def load_user_profile(self, user_id: str) -> Optional[Dict]:
        """Load user profile data."""
        try:
            profile_file = self.user_profiles_dir / f"user_{user_id}.json"
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return None