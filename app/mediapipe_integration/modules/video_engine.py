"""
Video Engine Module for MEMOTION.

Handles video playback, frame extraction, and synchronization.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Callable
from enum import Enum
import cv2
import time
import threading
from pathlib import Path
import numpy as np


class PlaybackState(Enum):
    """Video playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class VideoEngine:
    """
    Engine for video playback and frame management.
    """

    video_path: Optional[str] = None
    fps: float = 30.0
    current_frame: int = 0
    total_frames: int = 0
    state: PlaybackState = PlaybackState.STOPPED
    loop: bool = False

    # Internal
    _cap: Optional[cv2.VideoCapture] = None
    _thread: Optional[threading.Thread] = None
    _running: bool = False
    _callbacks: List[Callable] = field(default_factory=list)

    def __post_init__(self):
        if self.video_path and Path(self.video_path).exists():
            self.load_video(self.video_path)

    def load_video(self, video_path: str) -> bool:
        """
        Load video file.

        Args:
            video_path: Path to video file

        Returns:
            True if loaded successfully
        """
        if not Path(video_path).exists():
            return False

        self._cap = cv2.VideoCapture(video_path)
        if not self._cap.isOpened():
            return False

        self.video_path = video_path
        self.total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self._cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
        self.state = PlaybackState.STOPPED

        return True

    def play(self):
        """Start video playback."""
        if not self._cap or self.state == PlaybackState.PLAYING:
            return

        self.state = PlaybackState.PLAYING
        self._running = True

        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._playback_loop)
            self._thread.daemon = True
            self._thread.start()

    def pause(self):
        """Pause video playback."""
        self.state = PlaybackState.PAUSED

    def stop(self):
        """Stop video playback."""
        self.state = PlaybackState.STOPPED
        self._running = False
        self.current_frame = 0

        if self._cap:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def seek(self, frame_number: int):
        """Seek to specific frame."""
        if self._cap and 0 <= frame_number < self.total_frames:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current frame as numpy array."""
        if not self._cap:
            return None

        ret, frame = self._cap.read()
        if ret:
            self.current_frame += 1
            return frame
        else:
            if self.loop:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame = 0
                ret, frame = self._cap.read()
                if ret:
                    self.current_frame = 1
                    return frame

        return None

    def add_frame_callback(self, callback: Callable):
        """Add callback for new frames."""
        self._callbacks.append(callback)

    def _playback_loop(self):
        """Main playback loop."""
        frame_time = 1.0 / self.fps

        while self._running:
            if self.state == PlaybackState.PLAYING:
                start_time = time.time()

                frame = self.get_current_frame()
                if frame is not None:
                    # Call callbacks
                    for callback in self._callbacks:
                        callback(frame, self.current_frame)

                    # Wait for next frame
                    elapsed = time.time() - start_time
                    if elapsed < frame_time:
                        time.sleep(frame_time - elapsed)
                else:
                    # End of video
                    if not self.loop:
                        self.state = PlaybackState.COMPLETED
                        self._running = False
                    else:
                        self.current_frame = 0
            else:
                time.sleep(0.1)  # Sleep when paused

    def __del__(self):
        """Cleanup resources."""
        self._running = False
        if self._cap:
            self._cap.release()