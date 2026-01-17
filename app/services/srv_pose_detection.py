"""
Pose Detection Service for Memotion Backend

High-level service that manages pose detection sessions and integrates
with the pose detection agent for real-time processing.
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..ai_agent.pose_detection_agent import PoseDetectionAgent
from ..core.config import settings


logger = logging.getLogger(__name__)


class PoseDetectionService:
    """
    Service for managing real-time pose detection sessions.
    Handles session lifecycle, frame processing, and feedback streaming.
    """

    def __init__(self):
        self.agent = PoseDetectionAgent()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.reference_videos: Dict[str, str] = {}  # exercise_id -> video_path

    async def initialize_exercise(self, exercise_id: str, video_path: str) -> bool:
        """
        Initialize reference video for an exercise.

        Args:
            exercise_id: Unique exercise identifier
            video_path: Path to reference video file

        Returns:
            bool: True if initialized successfully
        """
        # Convert relative path to absolute path
        abs_video_path = Path(video_path).resolve()
        if not abs_video_path.exists():
            logger.error(f"[SERVICE] Reference video not found: {video_path} (absolute: {abs_video_path})")
            return False

        success = self.agent.load_reference_video(exercise_id, str(abs_video_path))
        if success:
            self.reference_videos[exercise_id] = str(abs_video_path)
            logger.info(f"[SERVICE] Initialized exercise {exercise_id} with video {abs_video_path}")
        return success

    async def start_pose_session(self, task_id: str, exercise_id: str) -> Dict[str, Any]:
        """
        Start a new pose detection session.

        Args:
            task_id: Associated task identifier
            exercise_id: Exercise to perform

        Returns:
            Dict containing session information
        """
        logger.info(f"[POSE_SERVICE] Starting pose session for task {task_id}, exercise {exercise_id}")
        
        if exercise_id not in self.reference_videos:
            logger.error(f"[POSE_SERVICE] Exercise {exercise_id} not initialized. Available exercises: {list(self.reference_videos.keys())}")
            return {
                'code': '400',
                'message': f'Exercise {exercise_id} not initialized',
                'data': None
            }

        session_id = str(uuid.uuid4())
        logger.info(f"[POSE_SERVICE] Generated session_id: {session_id}")

        try:
            success = self.agent.start_session(session_id, exercise_id, task_id)
            logger.info(f"[POSE_SERVICE] Agent start_session result: {success}")
            if not success:
                return {
                    'code': '500',
                    'message': 'Failed to start pose detection session',
                    'data': None
                }
        except Exception as e:
            logger.error(f"[POSE_SERVICE] Error starting agent session: {e}", exc_info=True)
            return {
                'code': '500',
                'message': f'Failed to start pose detection session: {str(e)}',
                'data': None
            }

        self.active_sessions[session_id] = {
            'task_id': task_id,
            'exercise_id': exercise_id,
            'start_time': time.time(),
            'status': 'active'
        }

        # Generate WebRTC/WebSocket endpoints
        webrtc_offer = await self._generate_webrtc_offer(session_id)
        reference_video_url = self._get_reference_video_url(exercise_id)

        return {
            'code': '000',
            'message': 'Pose session started successfully',
            'data': {
                'session_id': session_id,
                'webrtc_offer': webrtc_offer,
                'reference_video_url': reference_video_url
            }
        }

    async def process_frame_stream(self, session_id: str, frame_data: bytes) -> Dict[str, Any]:
        """
        Process a frame from the video stream.

        Args:
            session_id: Active session identifier
            frame_data: Encoded frame data (JPEG/PNG)

        Returns:
            Dict containing processing results
        """
        # logger.info(f"[POSE_SERVICE] Received frame for session {session_id}, frame size: {len(frame_data)} bytes")

        if session_id not in self.active_sessions:
            return {
                'error': 'Session not found',
                'status': 'error'
            }

        # Process frame through agent
        result = self.agent.process_frame(session_id, frame_data)

        # Check if session completed
        if result.get('completed', False):
            await self.end_pose_session(session_id)

        return result

    async def end_pose_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a pose detection session.

        Args:
            session_id: Session to end

        Returns:
            Dict containing final session data
        """
        if session_id not in self.active_sessions:
            return {
                'code': '404',
                'message': 'Session not found',
                'data': None
            }

        session = self.active_sessions[session_id]

        # Get final status from agent
        final_status = self.agent.get_session_status(session_id)

        # End session in agent
        self.agent.end_session(session_id)

        # Calculate completion data
        completion_score = final_status.get('current_score', 0.0) if final_status else 0.0
        duration = time.time() - session['start_time']

        # Cleanup
        del self.active_sessions[session_id]

        return {
            'code': '000',
            'message': 'Session ended successfully',
            'data': {
                'session_id': session_id,
                'task_id': session['task_id'],
                'completion_score': completion_score,
                'duration_held': duration
            }
        }

    async def get_session_feedback(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current feedback for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict containing current feedback or None if session not found
        """
        if session_id not in self.active_sessions:
            return None

        return self.agent.get_session_status(session_id)

    async def _generate_webrtc_offer(self, session_id: str) -> str:
        """
        Generate WebRTC offer for the session.
        In a real implementation, this would set up WebRTC peer connection.
        """
        # Placeholder - in real implementation, integrate with aiortc
        return f"webrtc-offer-{session_id}"

    def _get_reference_video_url(self, exercise_id: str) -> str:
        """
        Get reference video URL for an exercise.
        """
        # Return the local video URL if the exercise is initialized
        if exercise_id in self.reference_videos:
            video_path = self.reference_videos[exercise_id]
            # Convert file path to URL path
            relative_path = str(Path(video_path).relative_to(Path.cwd()))
            return f"http://localhost:8000/{relative_path.replace(chr(92), '/')}"
        
        # Fallback for uninitialized exercises
        return f"http://localhost:8000/static/uploads/exercise/{exercise_id}.mp4"

    async def cleanup_expired_sessions(self):
        """
        Cleanup sessions that have been inactive for too long.
        """
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if current_time - session['start_time'] > 3600:  # 1 hour timeout
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            print(f"[SERVICE] Cleaning up expired session {session_id}")
            await self.end_pose_session(session_id)


# Global service instance
pose_detection_service = PoseDetectionService()