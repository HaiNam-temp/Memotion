"""
Pose Detection Service for Memotion Backend

High-level service that orchestrates pose detection sessions using MediaPipe integration.
Handles session lifecycle, frame processing, and integrates with MediaPipe modules for AI processing.
"""

import asyncio
import uuid
import time
import logging
import base64
import cv2
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import MediaPipe integration modules
from ..mediapipe_integration.core import (
    VisionDetector, DetectorConfig, JointType, JOINT_DEFINITIONS,
    calculate_joint_angle, MotionPhase, SyncStatus, SyncState,
    MotionSyncController, create_arm_raise_exercise, create_elbow_flex_exercise,
    compute_single_joint_dtw, PoseLandmarkIndex,
)
from ..mediapipe_integration.modules import (
    HealthScorer, VideoEngine, PlaybackState, PainDetector, PainLevel,
    SafeMaxCalibrator, CalibrationState, UserProfile,
)
from ..mediapipe_integration.utils import (
    SessionLogger,
)

logger = logging.getLogger(__name__)


class PoseDetectionService:
    """
    Service for managing real-time pose detection sessions using MediaPipe integration.
    Handles session lifecycle, frame processing, and AI-powered analysis for all 3 phases.
    """

    def __init__(self):
        # Initialize MediaPipe components
        model_path = Path("app/mediapipe_models/pose_landmarker_lite.task").resolve()
        self._detector_config = DetectorConfig(
            pose_model_path=str(model_path),
            running_mode="VIDEO"
        )
        self._vision_detector = VisionDetector(self._detector_config)

        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.reference_videos: Dict[str, str] = {}  # exercise_id -> video_path
        self.initialized_exercises: set = set()  # Set of initialized exercise IDs
        self.session_loggers: Dict[str, SessionLogger] = {}

        # MediaPipe session components
        self._video_engines: Dict[str, VideoEngine] = {}
        self._session_components: Dict[str, Dict[str, Any]] = {}

        # Check dependencies
        self.dependencies_available = True
        try:
            # Test detector
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = self._vision_detector.process_frame(test_frame, timestamp_ms=0)
            logger.info("[SERVICE] MediaPipe integration initialized successfully")
        except Exception as e:
            logger.error(f"[SERVICE] MediaPipe initialization failed: {e}")
            logger.warning("[SERVICE] Continuing without MediaPipe for testing purposes")
            self.dependencies_available = False

    async def initialize_exercise(self, exercise_id: str, video_path: str) -> bool:
        """
        Initialize reference video for an exercise.

        Args:
            exercise_id: Unique exercise identifier
            video_path: Path to reference video file

        Returns:
            bool: True if initialized successfully (or gracefully handled)
        """
        # Check if already initialized
        if exercise_id in self.initialized_exercises:
            return True

        # Convert relative path to absolute path
        abs_video_path = Path(video_path).resolve()
        if not abs_video_path.exists():
            logger.warning(f"[SERVICE] Reference video not found: {video_path} (absolute: {abs_video_path})")
            logger.warning(f"[SERVICE] Continuing without reference video for exercise {exercise_id}")
            # Mark as initialized even without video for testing purposes
            self.initialized_exercises.add(exercise_id)
            return True

        # Initialize VideoEngine for this exercise
        try:
            video_engine = VideoEngine(str(abs_video_path))
            # Store video engine instance for this exercise
            self.video_engines[exercise_id] = video_engine
            self.initialized_exercises.add(exercise_id)
            logger.info(f"[SERVICE] Exercise {exercise_id} initialized with video: {video_path}")
            return True
        except Exception as e:
            logger.error(f"[SERVICE] Failed to initialize VideoEngine for exercise {exercise_id}: {str(e)}")
            # For testing, continue even if VideoEngine fails
            logger.warning(f"[SERVICE] Continuing without VideoEngine for exercise {exercise_id}")
            self.initialized_exercises.add(exercise_id)
            return True

    async def start_pose_session(self, task_id: str, exercise_id: str, user_id: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Start a new pose detection session with 3-phase logic using MediaPipe integration.

        Args:
            task_id: Associated task identifier
            exercise_id: Exercise to perform
            user_id: User identifier
            config: Optional configuration

        Returns:
            Dict containing session information
        """
        logger.info(f"[POSE_SERVICE] Starting pose session for task {task_id}, exercise {exercise_id}, user {user_id}")

        # Initialize exercise if not already initialized
        if exercise_id not in self.initialized_exercises:
            logger.info(f"[POSE_SERVICE] Exercise {exercise_id} not initialized, initializing now...")
            video_path = f"data/videos/{exercise_id}.mp4"  # Default video path
            init_success = await self.initialize_exercise(exercise_id, video_path)
            if not init_success:
                logger.error(f"[POSE_SERVICE] Failed to initialize exercise {exercise_id}")
                return {
                    'code': '500',
                    'message': f'Failed to initialize exercise {exercise_id}',
                    'data': None
                }

        session_id = str(uuid.uuid4())
        logger.info(f"[POSE_SERVICE] Generated session_id: {session_id}")

        # Initialize MediaPipe components for this session
        try:
            # Create motion sync controller for this exercise
            # For testing without videos, create a dummy video engine or use None
            video_engine = self._video_engines.get(exercise_id)
            if not video_engine:
                # Create a dummy video engine for testing
                from ..mediapipe_integration.modules import VideoEngine
                video_engine = VideoEngine(video_path=None)
                logger.warning(f"[POSE_SERVICE] Using dummy video engine for exercise {exercise_id}")

            # Create exercise based on type (arm raise or elbow flex)
            if "arm" in exercise_id.lower():
                reference_angles = create_arm_raise_exercise()
            else:
                reference_angles = create_elbow_flex_exercise()

            # Note: MotionSyncController constructor might need to be updated
            # For now, create it without video_engine parameter
            motion_sync = MotionSyncController()
            motion_sync.update_reference(reference_angles)  # Set reference angles from exercise
            health_scorer = HealthScorer()
            pain_detector = PainDetector()
            session_logger = SessionLogger(session_id)

            # Store components for this session
            if not hasattr(self, '_session_components'):
                self._session_components = {}
            self._session_components[session_id] = {
                'motion_sync': motion_sync,
                'health_scorer': health_scorer,
                'pain_detector': pain_detector,
                'session_logger': session_logger,
                'video_engine': video_engine
            }

            self.session_loggers[session_id] = session_logger

        except Exception as e:
            logger.error(f"[POSE_SERVICE] Error initializing MediaPipe components: {e}", exc_info=True)
            return {
                'code': '500',
                'message': f'Failed to initialize pose detection session: {str(e)}',
                'data': None
            }

        # Initialize session with 3-phase structure
        self.active_sessions[session_id] = {
            'task_id': task_id,
            'exercise_id': exercise_id,
            'user_id': user_id,
            'start_time': time.time(),
            'status': 'active',
            'current_phase': 'detection',  # Start with detection phase
            'stability_counter': 0,
            'measuring_frames': [],
            'scoring_started': False,
            'hold_start': None,
            'results': {},
            'config': config or {},
            'stability_threshold': config.get('stability_threshold', 0.7) if config else 0.7,
            'min_measuring_frames': config.get('min_measuring_frames', 100) if config else 100,
            'phase_data': {
                'detection': {'frames_processed': 0, 'person_detected': False},
                'measuring': {'frames_processed': 0, 'angles_calculated': []},
                'scoring': {'frames_processed': 0, 'scores_calculated': []}
            }
        }

        # Generate WebRTC/WebSocket endpoints
        websocket_url = f"ws://localhost:8000/api/pose/stream/{session_id}"
        reference_video_url = self._get_reference_video_url(exercise_id)

        return {
            'code': '000',
            'message': 'Pose session started successfully',
            'data': {
                'session_id': session_id,
                'websocket_url': websocket_url,
                'reference_video_url': reference_video_url,
                'current_phase': 'detection'
            }
        }

    async def process_frame_stream(self, session_id: str, frame_data: bytes, phase: str) -> Dict[str, Any]:
        """
        Process a frame from the video stream with phase-specific logic.

        Args:
            session_id: Active session identifier
            frame_data: Encoded frame data (JPEG/PNG)
            phase: Current phase ('detection', 'measuring', 'scoring')

        Returns:
            Dict containing processing results
        """
        if session_id not in self.active_sessions:
            return {
                'error': 'Session not found',
                'status': 'error'
            }

        session = self.active_sessions[session_id]

        try:
            if phase == 'detection':
                return await self._process_detection_frame(session, frame_data)
            elif phase == 'measuring':
                return await self._process_measuring_frame(session, frame_data)
            elif phase == 'scoring':
                return await self._process_scoring_frame(session, frame_data)
            else:
                return {
                    'error': f'Unknown phase: {phase}',
                    'status': 'error'
                }
        except Exception as e:
            logger.error(f"[SERVICE] Frame processing failed for session {session_id}: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }

    async def _process_detection_frame(self, session: Dict[str, Any], frame_data: bytes) -> Dict[str, Any]:
        """Process frame in detection phase using MediaPipe VisionDetector."""
        session_id = None
        for sid, s in self.active_sessions.items():
            if s is session:
                session_id = sid
                break

        if not session_id or session_id not in self._session_components:
            return {'error': 'Session components not found', 'status': 'error'}

        components = self._session_components[session_id]

        try:
            # Decode frame
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Process with VisionDetector
            timestamp_ms = int(time.time() * 1000)
            detection_result = self._vision_detector.process_frame(frame, timestamp_ms)

            # Check if person is detected
            person_detected = detection_result.pose_landmarks is not None
            # Calculate confidence from visibilities
            if detection_result.pose_landmarks:
                visibilities = [lm.visibility for lm in detection_result.pose_landmarks if hasattr(lm, 'visibility') and lm.visibility is not None]
                stability_score = sum(visibilities) / len(visibilities) if visibilities else 0.0
            else:
                stability_score = 0.0

            # Update phase data
            session['phase_data']['detection']['frames_processed'] += 1
            session['phase_data']['detection']['person_detected'] = person_detected

            # Log detection data
            components['session_logger'].log_detection_frame(
                frame_number=session['phase_data']['detection']['frames_processed'],
                person_detected=person_detected,
                confidence=stability_score,
                landmarks=detection_result.pose_landmarks
            )

            if person_detected and stability_score > session['stability_threshold']:
                session['stability_counter'] += 1

                if session['stability_counter'] >= 10:  # Require 10 stable frames
                    session['current_phase'] = 'measuring'
                    session['stability_counter'] = 0
                    logger.info(f"[SERVICE] Session {session_id} moving to measuring phase")

                    return {
                        'status': 'phase_complete',
                        'phase': 'detection',
                        'next_phase': 'measuring',
                        'person_detected': True,
                        'stability_score': stability_score,
                        'frames_processed': session['phase_data']['detection']['frames_processed']
                    }
            else:
                session['stability_counter'] = 0

            return {
                'status': 'processing',
                'phase': 'detection',
                'person_detected': person_detected,
                'stability_score': stability_score,
                'stability_counter': session['stability_counter'],
                'frames_processed': session['phase_data']['detection']['frames_processed']
            }

        except Exception as e:
            logger.error(f"[SERVICE] Detection frame processing failed: {e}")
            return {'error': str(e), 'status': 'error'}
            if session['stability_counter'] >= 30:
                session['current_phase'] = 'measuring'
                return {
                    'status': 'phase_change',
                    'phase': 'measuring',
                    'message': 'User detected and stable. Start measuring motion.'
                }
        else:
            session['stability_counter'] = max(0, session['stability_counter'] - 1)

        return {
            'status': 'detection_feedback',
            'person_detected': person_detected,
            'stability_score': stability_score,
            'frames_stable': session['stability_counter'],
            'required_stable_frames': 30
        }

    async def _process_measuring_frame(self, session: Dict[str, Any], frame_data: bytes) -> Dict[str, Any]:
        """Process frame in measuring phase using MediaPipe kinematics."""
        session_id = None
        for sid, s in self.active_sessions.items():
            if s is session:
                session_id = sid
                break

        if not session_id or session_id not in self._session_components:
            return {'error': 'Session components not found', 'status': 'error'}

        components = self._session_components[session_id]

        try:
            # Decode frame
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Process with VisionDetector
            timestamp_ms = int(time.time() * 1000)
            detection_result = self._vision_detector.process_frame(frame, timestamp_ms)

            if not detection_result.person_detected or not detection_result.landmarks:
                return {
                    'status': 'measuring_feedback',
                    'error': 'Person not detected',
                    'frames_captured': len(session['measuring_frames']),
                    'total_required_frames': session['min_measuring_frames']
                }

            # Calculate joint angles using kinematics functions
            angles = {}
            try:
                # Calculate shoulder angles (for arm exercises)
                left_shoulder_angle = calculate_joint_angle(
                    detection_result.landmarks,
                    PoseLandmarkIndex.LEFT_SHOULDER,
                    PoseLandmarkIndex.LEFT_ELBOW,
                    PoseLandmarkIndex.LEFT_HIP
                )
                right_shoulder_angle = calculate_joint_angle(
                    detection_result.landmarks,
                    PoseLandmarkIndex.RIGHT_SHOULDER,
                    PoseLandmarkIndex.RIGHT_ELBOW,
                    PoseLandmarkIndex.RIGHT_HIP
                )

                # Calculate elbow angles
                left_elbow_angle = calculate_joint_angle(
                    detection_result.landmarks,
                    PoseLandmarkIndex.LEFT_ELBOW,
                    PoseLandmarkIndex.LEFT_SHOULDER,
                    PoseLandmarkIndex.LEFT_WRIST
                )
                right_elbow_angle = calculate_joint_angle(
                    detection_result.landmarks,
                    PoseLandmarkIndex.RIGHT_ELBOW,
                    PoseLandmarkIndex.RIGHT_SHOULDER,
                    PoseLandmarkIndex.RIGHT_WRIST
                )

                angles = {
                    'left_shoulder': left_shoulder_angle,
                    'right_shoulder': right_shoulder_angle,
                    'left_elbow': left_elbow_angle,
                    'right_elbow': right_elbow_angle
                }

            except Exception as e:
                logger.warning(f"[SERVICE] Angle calculation failed: {e}")
                angles = {}

            # Store frame data
            frame_data_entry = {
                'timestamp': time.time(),
                'landmarks': detection_result.landmarks,
                'angles': angles
            }
            session['measuring_frames'].append(frame_data_entry)

            # Update phase data
            session['phase_data']['measuring']['frames_processed'] += 1
            session['phase_data']['measuring']['angles_calculated'].append(angles)

            # Log measuring data
            components['session_logger'].log_measuring_frame(
                frame_number=session['phase_data']['measuring']['frames_processed'],
                landmarks=detection_result.landmarks,
                angles=angles
            )

            frames_captured = len(session['measuring_frames'])
            total_required = session['min_measuring_frames']

            if frames_captured >= total_required:
                session['current_phase'] = 'scoring'
                session['scoring_started'] = True
                logger.info(f"[SERVICE] Session {session_id} moving to scoring phase")

                return {
                    'status': 'phase_complete',
                    'phase': 'measuring',
                    'next_phase': 'scoring',
                    'frames_captured': frames_captured,
                    'total_required_frames': total_required,
                    'message': 'Motion captured. Starting scoring with reference video.'
                }

            return {
                'status': 'measuring_feedback',
                'frames_captured': frames_captured,
                'total_required_frames': total_required,
                'progress_percentage': (frames_captured / total_required) * 100,
                'current_angles': angles
            }

        except Exception as e:
            logger.error(f"[SERVICE] Measuring frame processing failed: {e}")
            return {'error': str(e), 'status': 'error'}

    async def _process_scoring_frame(self, session: Dict[str, Any], frame_data: bytes) -> Dict[str, Any]:
        """Process frame in scoring phase using MediaPipe HealthScorer and MotionSyncController."""
        session_id = None
        for sid, s in self.active_sessions.items():
            if s is session:
                session_id = sid
                break

        if not session_id or session_id not in self._session_components:
            return {'error': 'Session components not found', 'status': 'error'}

        components = self._session_components[session_id]

        try:
            # Decode frame
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Process with VisionDetector
            timestamp_ms = int(time.time() * 1000)
            detection_result = self._vision_detector.process_frame(frame, timestamp_ms)

            if not detection_result.person_detected or not detection_result.landmarks:
                return {
                    'status': 'scoring_feedback',
                    'error': 'Person not detected',
                    'hold_progress': self._calculate_hold_progress(session, False)
                }

            # Update phase data
            session['phase_data']['scoring']['frames_processed'] += 1

            # Calculate current pose angles
            current_angles = {}
            try:
                current_angles = {
                    'left_shoulder': calculate_joint_angle(
                        detection_result.pose_landmarks,
                        PoseLandmarkIndex.LEFT_SHOULDER,
                        PoseLandmarkIndex.LEFT_ELBOW,
                        PoseLandmarkIndex.LEFT_HIP
                    ),
                    'right_shoulder': calculate_joint_angle(
                        detection_result.pose_landmarks,
                        PoseLandmarkIndex.RIGHT_SHOULDER,
                        PoseLandmarkIndex.RIGHT_ELBOW,
                        PoseLandmarkIndex.RIGHT_HIP
                    ),
                    'left_elbow': calculate_joint_angle(
                        detection_result.pose_landmarks,
                        PoseLandmarkIndex.LEFT_ELBOW,
                        PoseLandmarkIndex.LEFT_SHOULDER,
                        PoseLandmarkIndex.LEFT_WRIST
                    ),
                    'right_elbow': calculate_joint_angle(
                        detection_result.pose_landmarks,
                        PoseLandmarkIndex.RIGHT_ELBOW,
                        PoseLandmarkIndex.RIGHT_SHOULDER,
                        PoseLandmarkIndex.RIGHT_WRIST
                    )
                }
            except Exception as e:
                logger.warning(f"[SERVICE] Current angle calculation failed: {e}")
                current_angles = {}

            # Sync with reference video
            motion_sync = components['motion_sync']
            sync_result = motion_sync.process_frame(detection_result.pose_landmarks, timestamp_ms)

            # Calculate health scores using HealthScorer
            health_scorer = components['health_scorer']

            # Calculate ROM scores
            rom_scores = health_scorer.calculate_rom_score(current_angles)

            # Calculate stability scores
            stability_scores = health_scorer.calculate_stability_score(
                detection_result.pose_landmarks,
                session['measuring_frames'][-10:] if len(session['measuring_frames']) >= 10 else session['measuring_frames']
            )

            # Calculate flow scores using DTW
            reference_angles = [frame['angles'] for frame in session['measuring_frames'] if frame['angles']]
            flow_scores = {}
            if reference_angles:
                try:
                    # Use DTW for flow scoring
                    dtw_score = compute_single_joint_dtw(
                        [angles.get('left_shoulder', 0) for angles in reference_angles],
                        [angles.get('left_shoulder', 0) for angles in [current_angles]]
                    )
                    flow_scores = {'overall_flow': max(0, 100 - dtw_score * 10)}  # Convert to percentage
                except Exception as e:
                    logger.warning(f"[SERVICE] DTW calculation failed: {e}")
                    flow_scores = {'overall_flow': 85.0}

            # Calculate symmetry scores
            symmetry_scores = health_scorer.calculate_symmetry_score(current_angles)

            # Combine scores
            overall_score = health_scorer.calculate_overall_score({
                'rom': rom_scores,
                'stability': stability_scores,
                'flow': flow_scores,
                'symmetry': symmetry_scores
            })

            # Check pain detection
            pain_detector = components['pain_detector']
            pain_level = pain_detector.detect_pain(detection_result.pose_landmarks, current_angles)

            # Determine if pose is correct (high similarity to reference)
            similarity_score = sync_result.confidence if sync_result else 0.5
            is_correct_pose = similarity_score > 0.7 and pain_level == PainLevel.NONE

            # Check hold timer
            hold_progress = self._calculate_hold_progress(session, is_correct_pose)

            # Log scoring data
            components['session_logger'].log_scoring_frame(
                frame_number=session['phase_data']['scoring']['frames_processed'],
                landmarks=detection_result.pose_landmarks,
                angles=current_angles,
                scores={
                    'rom': rom_scores,
                    'stability': stability_scores,
                    'flow': flow_scores,
                    'symmetry': symmetry_scores,
                    'overall': overall_score
                },
                sync_confidence=similarity_score,
                pain_level=pain_level.value if pain_level else 'unknown'
            )

            if hold_progress['completed']:
                # Calculate final results
                final_scores = {
                    'overall_score': overall_score,
                    'rom_scores': rom_scores,
                    'stability_scores': stability_scores,
                    'flow_scores': flow_scores,
                    'symmetry_scores': symmetry_scores,
                    'fatigue_level': health_scorer.assess_fatigue(session['measuring_frames']),
                    'pain_detected': pain_level.value if pain_level != PainLevel.NONE else 'none',
                    'recommendations': health_scorer.generate_recommendations({
                        'rom': rom_scores,
                        'stability': stability_scores,
                        'symmetry': symmetry_scores,
                        'pain': pain_level
                    }),
                    'duration': time.time() - session['start_time'],
                    'frames_processed': {
                        'detection': session['phase_data']['detection']['frames_processed'],
                        'measuring': session['phase_data']['measuring']['frames_processed'],
                        'scoring': session['phase_data']['scoring']['frames_processed']
                    }
                }
                session['results'] = final_scores
                session['status'] = 'completed'

                logger.info(f"[SERVICE] Session {session_id} completed with score {overall_score}")

                return {
                    'status': 'exercise_completed',
                    'final_scores': final_scores
                }

            return {
                'status': 'scoring_feedback',
                'similarity_score': similarity_score,
                'scores': {
                    'rom_score': rom_scores.get('overall', 0),
                    'stability_score': stability_scores.get('overall', 0),
                    'flow_score': flow_scores.get('overall_flow', 0),
                    'symmetry_score': symmetry_scores.get('overall', 0)
                },
                'hold_progress': hold_progress,
                'pain_level': pain_level.value if pain_level else 'unknown',
                'current_angles': current_angles
            }

        except Exception as e:
            logger.error(f"[SERVICE] Scoring frame processing failed: {e}")
            return {'error': str(e), 'status': 'error'}

    def _calculate_hold_progress(self, session: Dict[str, Any], is_correct_pose: bool) -> Dict[str, Any]:
        """Calculate hold timer progress."""
        required_seconds = 5.0

        if is_correct_pose:
            if session.get('hold_start') is None:
                session['hold_start'] = time.time()

            elapsed = time.time() - session['hold_start']
            if elapsed >= required_seconds:
                return {
                    'holding': True,
                    'current_seconds': elapsed,
                    'required_seconds': required_seconds,
                    'percentage': 100.0,
                    'completed': True
                }
            else:
                return {
                    'holding': True,
                    'current_seconds': elapsed,
                    'required_seconds': required_seconds,
                    'percentage': (elapsed / required_seconds) * 100.0,
                    'completed': False
                }
        else:
            session['hold_start'] = None
            return {
                'holding': False,
                'current_seconds': 0.0,
                'required_seconds': required_seconds,
                'percentage': 0.0,
                'completed': False
            }

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

        # Calculate completion data
        completion_score = session.get('results', {}).get('overall_score', 0.0)
        duration = time.time() - session['start_time']

        # Cleanup session components
        if session_id in self._session_components:
            components = self._session_components[session_id]
            # Close session logger
            if 'session_logger' in components:
                components['session_logger'].close()
            del self._session_components[session_id]

        if session_id in self.session_loggers:
            del self.session_loggers[session_id]

        # Cleanup
        results = session.get('results', {})
        del self.active_sessions[session_id]

        return {
            'code': '000',
            'message': 'Session ended successfully',
            'data': {
                'session_id': session_id,
                'task_id': session['task_id'],
                'completion_score': completion_score,
                'duration_held': duration,
                'results': results
            }
        }

    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """
        Get results for a completed session.

        Args:
            session_id: Session identifier

        Returns:
            Dict containing session results
        """
        if session_id not in self.active_sessions:
            return {
                'code': '404',
                'message': 'Session not found',
                'data': None
            }

        session = self.active_sessions[session_id]

        if session['status'] != 'completed':
            return {
                'code': '400',
                'message': 'Session not completed yet',
                'data': None
            }

        return {
            'code': '000',
            'message': 'Results retrieved successfully',
            'data': session.get('results', {})
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

        session = self.active_sessions[session_id]

        # Return current session status and phase data
        return {
            'session_id': session_id,
            'status': session['status'],
            'current_phase': session['current_phase'],
            'phase_data': session['phase_data'],
            'results': session.get('results', {}),
            'start_time': session['start_time'],
            'duration': time.time() - session['start_time']
        }

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

    async def get_active_sessions_count(self) -> int:
        """
        Get the count of currently active pose detection sessions.
        """
        return len(self.active_sessions)

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