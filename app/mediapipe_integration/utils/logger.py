"""
Logger Module for MEMOTION.

Session logging functionality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import time
from pathlib import Path


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogCategory(Enum):
    """Log categories."""
    POSE = "pose"
    SYNC = "sync"
    SCORE = "score"
    PAIN = "pain"
    SYSTEM = "system"


@dataclass
class LogEntry:
    """Log entry."""
    timestamp: float
    level: LogLevel
    category: LogCategory
    message: str
    data: Optional[Dict] = None


@dataclass
class SessionLogger:
    """
    Logger for exercise sessions.
    """

    session_id: str
    log_dir: str = "./data/logs"
    entries: List[LogEntry] = field(default_factory=list)

    def __post_init__(self):
        self.log_dir = Path(self.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, level: LogLevel, category: LogCategory, message: str, data: Optional[Dict] = None):
        """
        Log a message.

        Args:
            level: Log level
            category: Log category
            message: Log message
            data: Optional data
        """
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            category=category,
            message=message,
            data=data
        )
        self.entries.append(entry)

    def info(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log info message."""
        self.log(LogLevel.INFO, category, message, data)

    def warning(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log warning message."""
        self.log(LogLevel.WARNING, category, message, data)

    def error(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log error message."""
        self.log(LogLevel.ERROR, category, message, data)

    def log_detection_frame(self, frame_number: int, person_detected: bool, confidence: float, landmarks: Optional[Any] = None):
        """Log detection frame data."""
        data = {
            'frame_number': frame_number,
            'person_detected': person_detected,
            'confidence': confidence,
        }
        if landmarks:
            # Convert landmarks to serializable format
            data['landmarks'] = [
                {'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': getattr(lm, 'visibility', None), 'presence': getattr(lm, 'presence', None)}
                for lm in landmarks
            ] if hasattr(landmarks, '__iter__') else None
        self.info(LogCategory.POSE, f"Detection frame {frame_number}", data)

    def log_scoring_frame(self, frame_number: int, landmarks: Optional[Any] = None, angles: Optional[Dict] = None, scores: Optional[Dict] = None, sync_confidence: Optional[float] = None, pain_level: Optional[str] = None):
        """Log scoring frame data."""
        data = {
            'frame_number': frame_number,
        }
        if landmarks:
            data['landmarks'] = [
                {'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': getattr(lm, 'visibility', None), 'presence': getattr(lm, 'presence', None)}
                for lm in landmarks
            ] if hasattr(landmarks, '__iter__') else None
        if angles:
            data['angles'] = angles
        if scores:
            data['scores'] = scores
        if sync_confidence is not None:
            data['sync_confidence'] = sync_confidence
        if pain_level:
            data['pain_level'] = pain_level
        self.info(LogCategory.SCORE, f"Scoring frame {frame_number}", data)

    def save_session_log(self):
        """Save session log to file."""
        date_str = time.strftime("%Y%m%d")
        log_file = self.log_dir / f"session_{self.session_id}_{int(time.time())}.json"

        log_data = {
            'session_id': self.session_id,
            'timestamp': time.time(),
            'entries': [
                {
                    'timestamp': entry.timestamp,
                    'level': entry.level.value,
                    'category': entry.category.value,
                    'message': entry.message,
                    'data': entry.data
                }
                for entry in self.entries
            ]
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)


def create_session_logger(session_id: str, log_dir: str = "./data/logs") -> SessionLogger:
    """
    Create a session logger.

    Args:
        session_id: Session ID
        log_dir: Log directory

    Returns:
        SessionLogger instance
    """
    return SessionLogger(session_id, log_dir)