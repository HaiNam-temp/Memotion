"""
Pose Detection Service - Business Logic Layer (Simplified).

Real-time WebSocket only - minimal session management.
Calls MemotionEngine service (NO AI logic in this layer).

Author: MEMOTION Team
Version: 3.0.0
"""

from __future__ import annotations

import logging
import time
import base64
from typing import Dict, Optional, Any, List, TYPE_CHECKING
from pathlib import Path
import numpy as np
import cv2

from app.helpers.exception_handler import CustomException
from app.core.config import settings
from app.schemas.sche_pose import (
    StartSessionRequest, StartSessionResponse, ProcessFrameRequest,
    ProcessFrameResponse, SessionResultsResponse, PoseHealthResponse,
    PosePhase, SessionStatus
)

# Import Engine Service - NO AI logic implementation here
if TYPE_CHECKING:
    from app.mediapipe.mediapipe_be.service.engine_service import (
        MemotionEngine, EngineConfig
    )

# Runtime import with fallback
try:
    from app.mediapipe.mediapipe_be.service.engine_service import (
        MemotionEngine, EngineConfig
    )
    MEDIAPIPE_AVAILABLE = True
except ImportError as e:
    MEDIAPIPE_AVAILABLE = False
    logging.error(f"srv_pose: Failed to import MemotionEngine: {e}")


# ==================== CONSTANTS ====================

SERVICE_VERSION = "3.0.0"
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour


# ==================== SESSION CLASS ====================

class PoseSession:
    """Represents a single pose detection session."""
    
    def __init__(self, session_id: str, engine: Any, user_id: Optional[str] = None):
        self.session_id = session_id
        self.engine = engine
        self.user_id = user_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.status = SessionStatus.ACTIVE
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def is_expired(self, timeout: int = SESSION_TIMEOUT_SECONDS) -> bool:
        """Check if session has expired."""
        return time.time() - self.last_activity > timeout


# ==================== SERVICE CLASS ====================

class PoseDetectionService:
    """
    Service for pose detection operations.
    
    Manages sessions in memory, calls MemotionEngine for processing.
    Follows Clean Architecture: Business Logic Layer.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._sessions: Dict[str, PoseSession] = {}
        self._last_cleanup = time.time()
        self.logger.info("PoseDetectionService initialized")
    
    # ==================== SESSION MANAGEMENT ====================
    
    def start_session(self, request: StartSessionRequest) -> StartSessionResponse:
        """
        Start a new pose detection session.
        
        Returns session_id and websocket_url for real-time streaming.
        """
        self.logger.info(f"start_session: user_id={request.user_id}, exercise={request.exercise_type}")
        
        if not MEDIAPIPE_AVAILABLE:
            raise CustomException(http_code=503, code='503', message="MediaPipe service not available")
        
        # Cleanup expired sessions
        self._cleanup_expired_sessions()
        
        # Create engine config
        config = EngineConfig(
            models_dir=str(Path(settings.MEDIAPIPE_MODELS_DIR)),
            log_dir=str(Path(settings.MEDIAPIPE_LOG_DIR)),
            ref_video_path=request.ref_video_path,
            default_joint=request.default_joint
        )
        
        # Create engine instance
        try:
            engine = MemotionEngine.create_instance(config=config)
            self.logger.debug(f"start_session: Created MemotionEngine: {engine._state.instance_id}")
        except Exception as e:
            self.logger.error(f"start_session error: {e}", exc_info=True)
            raise CustomException(http_code=500, code='500', message=f"Failed to initialize engine: {str(e)}")
        
        # Generate session ID
        user_hash = hash(request.user_id or 'anonymous') % 10000
        session_id = f"pose_{int(time.time())}_{user_hash}"
        
        # Create and store session
        session = PoseSession(
            session_id=session_id,
            engine=engine,
            user_id=request.user_id
        )
        self._sessions[session_id] = session
        
        # Generate WebSocket URL
        websocket_url = f"/api/pose/sessions/{session_id}/ws"
        
        self.logger.info(f"start_session success: session_id={session_id}")
        
        return StartSessionResponse(
            session_id=session_id,
            status=SessionStatus.ACTIVE,
            current_phase=PosePhase.DETECTION,
            websocket_url=websocket_url,
            message="Session started. Connect to WebSocket for real-time streaming."
        )
    
    def get_session(self, session_id: str) -> PoseSession:
        """Get session by ID, validate not expired."""
        session = self._sessions.get(session_id)
        
        if not session:
            raise CustomException(http_code=404, code='404', message=f"Session not found: {session_id}")
        
        if session.is_expired():
            self._remove_session(session_id)
            raise CustomException(http_code=404, code='404', message=f"Session expired: {session_id}")
        
        session.update_activity()
        return session
    
    # ==================== FRAME PROCESSING ====================
    
    def process_frame(self, request: ProcessFrameRequest) -> ProcessFrameResponse:
        """
        Process a video frame through MemotionEngine.
        
        Called by WebSocket endpoint for real-time streaming.
        """
        session = self.get_session(request.session_id)
        
        # Decode frame
        try:
            frame = self._decode_frame(request.frame_data)
        except Exception as e:
            raise CustomException(http_code=400, code='400', message=f"Invalid frame data: {str(e)}")
        
        # Get timestamp (from request or generate current time)
        timestamp_ms = request.timestamp_ms if request.timestamp_ms else int(time.time() * 1000)
        
        # Process frame through engine (NO AI logic here - just forward)
        try:
            output = session.engine.process_frame(frame, timestamp_ms)
            output_dict = output.to_dict() if hasattr(output, 'to_dict') else output
        except Exception as e:
            self.logger.error(f"process_frame error: {e}", exc_info=True)
            raise CustomException(http_code=500, code='500', message=f"Engine processing failed: {str(e)}")
        
        # Extract response data
        phase = output_dict.get('phase', 1)
        phase_name = output_dict.get('phase_name', 'detection')
        data = self._extract_phase_data(output_dict)
        message = self._get_phase_message(output_dict)
        warning = output_dict.get('warning')
        
        return ProcessFrameResponse(
            session_id=request.session_id,
            phase=phase,
            phase_name=phase_name,
            data=data,
            message=message,
            warning=warning,
            timestamp=time.time()
        )
    
    def _decode_frame(self, frame_data: str) -> np.ndarray:
        """Decode base64 frame to numpy array."""
        # Remove data URI prefix if present
        if ',' in frame_data:
            frame_data = frame_data.split(',')[1]
        
        # Decode base64
        frame_bytes = base64.b64decode(frame_data)
        
        # Convert to numpy array
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Failed to decode image")
        
        return frame
    
    def _extract_phase_data(self, output_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract phase-specific data from engine output."""
        phase = output_dict.get('phase', 1)
        data = {}
        
        if phase == 1:  # Detection
            data = {
                'pose_detected': output_dict.get('pose_detected', False),
                'stable_count': output_dict.get('stable_count', 0),
                'progress': output_dict.get('progress', 0.0),
                'landmarks': output_dict.get('landmarks', [])
            }
        elif phase == 2:  # Calibration
            data = {
                'current_joint': output_dict.get('current_joint'),
                'current_joint_name': output_dict.get('current_joint_name'),
                'current_angle': output_dict.get('current_angle', 0.0),
                'max_angle': output_dict.get('max_angle', 0.0),
                'progress': output_dict.get('progress', 0.0)
            }
        elif phase == 3:  # Sync
            data = {
                'video_frame': output_dict.get('video_frame'),
                'current_score': output_dict.get('current_score', 0.0),
                'rep_count': output_dict.get('rep_count', 0),
                'fatigue_level': output_dict.get('fatigue_level', 'FRESH')
            }
        elif phase == 4:  # Scoring
            data = {
                'total_score': output_dict.get('total_score', 0.0),
                'rom_score': output_dict.get('rom_score', 0.0),
                'stability_score': output_dict.get('stability_score', 0.0),
                'flow_score': output_dict.get('flow_score', 0.0),
                'grade': output_dict.get('grade', '')
            }
        
        return data
    
    def _get_phase_message(self, output_dict: Dict[str, Any]) -> Optional[str]:
        """Get user-friendly message for current phase."""
        phase = output_dict.get('phase', 1)
        messages = {
            1: "Đang phát hiện tư thế...",
            2: "Đang hiệu chỉnh khớp...",
            3: "Đang đồng bộ với video...",
            4: "Hoàn thành!"
        }
        return output_dict.get('message') or messages.get(phase)
    
    # ==================== SESSION END ====================
    
    def end_session(self, session_id: str) -> SessionResultsResponse:
        """End session and return final results."""
        self.logger.info(f"end_session: session_id={session_id}")
        
        session = self.get_session(session_id)
        
        # Get final report from engine
        try:
            final_report = session.engine.get_final_report()
            report_dict = final_report.to_dict() if hasattr(final_report, 'to_dict') else final_report or {}
        except Exception as e:
            self.logger.warning(f"end_session: Failed to get final report: {e}")
            report_dict = {}
        
        # Cleanup engine
        try:
            session.engine.cleanup()
        except Exception as e:
            self.logger.warning(f"end_session: Engine cleanup failed: {e}")
        
        # Remove session
        self._remove_session(session_id)
        
        # Calculate duration
        duration = int(time.time() - session.created_at)
        
        self.logger.info(f"end_session success: session_id={session_id}, duration={duration}s")
        
        return SessionResultsResponse(
            session_id=session_id,
            exercise_name=report_dict.get('exercise_name', ''),
            duration_seconds=duration,
            total_score=report_dict.get('total_score', 0.0),
            rom_score=report_dict.get('rom_score', 0.0),
            stability_score=report_dict.get('stability_score', 0.0),
            flow_score=report_dict.get('flow_score', 0.0),
            grade=report_dict.get('grade', ''),
            grade_color=report_dict.get('grade_color', 'yellow'),
            total_reps=report_dict.get('total_reps', 0),
            fatigue_level=report_dict.get('fatigue_level', 'FRESH'),
            calibrated_joints=report_dict.get('calibrated_joints', []),
            rep_scores=report_dict.get('rep_scores', []),
            recommendations=report_dict.get('recommendations', [])
        )
    
    # ==================== HEALTH CHECK ====================
    
    def get_health(self) -> PoseHealthResponse:
        """Get service health status."""
        return PoseHealthResponse(
            status="healthy" if MEDIAPIPE_AVAILABLE else "degraded",
            mediapipe_available=MEDIAPIPE_AVAILABLE,
            active_sessions=len(self._sessions),
            version=SERVICE_VERSION
        )
    
    # ==================== INTERNAL METHODS ====================
    
    def _remove_session(self, session_id: str) -> None:
        """Remove session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self.logger.debug(f"_remove_session: Removed {session_id}")
    
    def _cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions. Returns count of removed sessions."""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        
        for sid in expired:
            try:
                session = self._sessions[sid]
                session.engine.cleanup()
            except:
                pass
            self._remove_session(sid)
        
        if expired:
            self.logger.info(f"_cleanup_expired_sessions: Removed {len(expired)} sessions")
        
        return len(expired)


# ==================== SINGLETON INSTANCE ====================

pose_detection_service = PoseDetectionService()
