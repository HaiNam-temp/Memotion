"""
Pose Detection API Module for MEMOTION Backend.

This module provides REST and WebSocket endpoints for real-time pose detection
with 3-phase logic (detection → measuring → scoring) for mobile applications.

**Authorization**: All endpoints require authenticated user access.

**Process**:
1. Start session with exercise configuration
2. Connect to WebSocket for real-time frame processing
3. Automatic phase transitions based on stability and frame collection
4. Retrieve results and end session

**Response**: All endpoints return standardized DataResponse format.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import threading
import time
from queue import Queue
import json
import os
import uuid
from pathlib import Path
import logging
import base64
import numpy as np
import cv2

# Import pose detection service
from ..services.srv_pose_detection import pose_detection_service

# Setup logging
logger = logging.getLogger(__name__)

# Import standard schemas and exceptions
from app.schemas.sche_base import DataResponse
from app.schemas.sche_pose_detection import (
    PoseDetectionSessionStartRequest,
    PoseDetectionSessionStartResponse,
    PoseDetectionResultsResponse,
    PoseDetectionSessionEndRequest,
    PoseDetectionSessionEndResponse,
    PoseDetectionHealthResponse,
)
from app.helpers.exception_handler import CustomException

# Import auth dependencies
from app.helpers.login_manager import login_required
from app.models.model_user import User

router = APIRouter(tags=["pose-detection"])

# Additional router for task-specific endpoints
task_router = APIRouter(prefix="/tasks", tags=["task-pose-detection"])

# Session storage (in production, use Redis)
active_sessions = {}

def map_exercise_id_to_type(exercise_id: str) -> str:
    """
    Map exercise_id (UUID or code) to exercise_type for service processing.
    """
    # Known mappings for UUIDs or codes
    exercise_mappings = {
        "d42e2a3c-8505-4734-ba46-629e5de3590d": "arm_raise",  # Add specific UUID mappings as needed
        "arm_raise_001": "arm_raise",
        "elbow_flex_001": "elbow_flex",
        # Add more mappings here as exercises are added
    }

    # Try exact match first
    if exercise_id in exercise_mappings:
        return exercise_mappings[exercise_id]

    # For unknown UUIDs, try to infer from patterns or default to arm_raise
    # You could add database lookup here if needed
    if len(exercise_id) == 36 and exercise_id.count('-') == 4:  # UUID format
        # For now, default unknown UUIDs to arm_raise
        # In production, you might want to look up the exercise type from database
        logger.warning(f"Unknown exercise UUID: {exercise_id}, defaulting to arm_raise")
        return "arm_raise"

    # For other formats, return as-is or default
    return exercise_id

from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import threading
import time
from queue import Queue
import json
import os
import uuid
from pathlib import Path
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Import từ mediapipe modules (sẽ được merge vào app)
try:
    # Giả sử mediapipe modules được copy vào app/mediapipe_integration/
    logger.info("Attempting to import MediaPipe modules...")
    from app.mediapipe.AI.service import (
        VisionDetector, DetectorConfig, JointType, JOINT_DEFINITIONS,
        calculate_joint_angle, MotionPhase, SyncStatus, SyncState,
        MotionSyncController, create_arm_raise_exercise, create_elbow_flex_exercise,
        compute_single_joint_dtw, PoseLandmarkIndex,
    )
    logger.info("Core modules imported successfully")

    # from app.mediapipe_integration.modules import (
    #     VideoEngine, PlaybackState, PainDetector, PainLevel,
    #     HealthScorer, FatigueLevel, SafeMaxCalibrator, CalibrationState,
    #     UserProfile,
    # )
    # logger.info("Modules imported successfully")

    from app.mediapipe.utils import (
        SessionLogger,
    )
    logger.info("Utils imported successfully")

    MEDIAPIPE_AVAILABLE = True
    logger.info("All MediaPipe modules imported successfully")
except ImportError as e:
    MEDIAPIPE_AVAILABLE = False
    logger.error(f"MediaPipe modules not available. Error: {e}")
    logger.error(f"Import error details: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    print(f"MediaPipe import failed: {e}")
    print(f"Traceback: {traceback.format_exc()}")

# Import auth dependencies
from app.helpers.login_manager import login_required
from app.models.model_user import User

router = APIRouter(tags=["pose-detection"])

# Additional router for task-specific endpoints
task_router = APIRouter(prefix="/tasks", tags=["task-pose-detection"])

# Session storage (in production, use Redis)
active_sessions = {}

@router.post("/start-session", response_model=DataResponse[PoseDetectionSessionStartResponse])
async def start_pose_session(
    request: PoseDetectionSessionStartRequest,
    current_user: User = Depends(login_required)
):
    """
    Start a new pose detection session for mobile 3-screen logic.

    This API initializes a pose detection session with automatic phase transitions
    (detection → measuring → scoring) for real-time exercise analysis.

    **Authorization**: User authentication required.

    **Process**:
    1. Validates user permissions and exercise/task existence
    2. Initializes MediaPipe detector and session components
    3. Creates WebSocket endpoint for real-time frame processing
    4. Sets up 3-phase processing pipeline with automatic transitions

    **Response**: Session details including WebSocket URL and initial phase.
    """
    # Temporarily disable MediaPipe check for testing
    # if not MEDIAPIPE_AVAILABLE:
    #     raise CustomException(
    #         http_code=503,
    #         code='503',
    #         message="Pose detection service unavailable - MediaPipe modules not loaded"
    #     )

    try:
        # Use provided task_id or generate a default one
        task_id = request.task_id or f"task_{uuid.uuid4()}"

        # Map exercise_type to exercise_id for internal processing
        exercise_id = map_exercise_id_to_type(request.exercise_type)

        # Prepare config for service
        config = {
            "stability_threshold": request.stability_threshold,
            "min_measuring_frames": request.min_measuring_frames,
            "duration_minutes": request.duration_minutes,
            "camera_source": request.camera_source,
            "model_complexity": request.model_complexity,
            "auto_phase_transition": request.auto_phase_transition,
        }

        # Call service to start session
        service_response = await pose_detection_service.start_pose_session(
            task_id=task_id,
            exercise_id=exercise_id,
            user_id=current_user.user_id,
            config=config
        )

        if service_response.get('code') != '000':
            raise CustomException(
                http_code=500,
                code='500',
                message=service_response.get('message', 'Failed to start session')
            )

        session_data = service_response.get('data', {})
        session_id = session_data.get('session_id')

        # Reference video URL
        reference_video_url = f"http://localhost:8000/data/videos/{exercise_id}.mp4" if request.reference_video_path else None

        logger.info(f"Started pose session {session_id} for user {current_user.user_id}, exercise {exercise_id}")

        response_data = PoseDetectionSessionStartResponse(
            session_id=session_id,
            websocket_url=session_data.get('websocket_url'),
            reference_video_url=reference_video_url,
            current_phase=session_data.get('current_phase', 'detection'),
            current_screen="screen_1"  # Phase 1 starts on screen 1
        )

        return DataResponse[PoseDetectionSessionStartResponse]().success_response(response_data)

    except CustomException:
        raise
    except Exception as e:
        logger.error(f"Failed to start pose session: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f"Failed to start pose detection session: {str(e)}"
        )

@router.websocket("/stream/{session_id}")
async def pose_stream_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint cho real-time pose detection với logic 3 màn hình.

    Logic xử lý theo chiến lược:
    Phase 1: Detection - Phát hiện người và ổn định
    Phase 2: Measuring - Thu thập cử động tự do
    Phase 3: Scoring - So sánh với video mẫu và chấm điểm
    """
    await websocket.accept()

    # Check if session exists in service
    session_feedback = await pose_detection_service.get_session_feedback(session_id)
    if not session_feedback:
        logger.error(f"WebSocket session {session_id} not found in service")
        await websocket.send_json({
            "type": "error",
            "error_code": "INVALID_SESSION",
            "message": "Session not found"
        })
        await websocket.close()
        return

    logger.info(f"WebSocket connected for session {session_id}")

    try:
        while session_feedback.get("status") == "active":
            # Nhận message từ mobile
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                # logger.info(f"Received WebSocket message: {data}") # Disabled verbose logging
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
                continue

            message_type = data.get("type")

            if message_type == "frame_data":
                frame_id = data.get("frame_id", 0)
                # Remove verbose logging here, will log in _handle_frame_data
                await _handle_frame_data(websocket, session_id, data)

            elif message_type == "request_phase_change":
                await _handle_phase_change_request(websocket, session_id, data)

            elif message_type == "end_session":
                await _handle_end_session(websocket, session_id, data)
                break

            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    "type": "error",
                    "error_code": "UNKNOWN_MESSAGE_TYPE",
                    "message": f"Unknown message type: {message_type}"
                })

            # Update session status
            session_feedback = await pose_detection_service.get_session_feedback(session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "error_code": "INTERNAL_ERROR",
                "message": "Internal server error"
            })
        except:
            pass

async def _handle_frame_data(websocket: WebSocket, session_id: str, data: Dict[str, Any]):
    """Xử lý frame data từ mobile theo 3 phases."""
    # Get current phase from service
    session_feedback = await pose_detection_service.get_session_feedback(session_id)
    if not session_feedback:
        await websocket.send_json({
            "type": "error",
            "error_code": "INVALID_SESSION",
            "message": "Session not found"
        })
        return

    current_phase = session_feedback.get("current_phase", "detection")

    frame_data = data.get("frame_data")  # base64 encoded frame
    frame_id = data.get("frame_id", 0)
    timestamp = data.get("timestamp", time.time())

    # Log request
    logger.info(f"[Phase {current_phase.capitalize()} - Request] - Frame {frame_id} received for session {session_id}")

    # Log process
    logger.info(f"[Phase {current_phase.capitalize()} - Process] - Processing frame {frame_id} in phase {current_phase}")

    if not frame_data:
        logger.warning(f"⚠️ [BACKEND] No frame data received for session {session_id}")
        return

    try:
        # Process frame through service
        result = await pose_detection_service.process_frame_stream(session_id, frame_data.encode(), current_phase)

        if result.get('status') == 'error':
            logger.error(f"[SERVICE] Frame processing failed: {result.get('error')}")
            await websocket.send_json({
                "type": "error",
                "error_code": "FRAME_PROCESSING_FAILED",
                "message": result.get('error', 'Unknown error')
            })
            return

        # Send appropriate response based on result
        if result.get('status') == 'phase_complete':
            # Phase transition occurred
            response = {
                "type": "phase_change",
                "phase": result.get('next_phase'),
                "screen": "screen_1" if result.get('next_phase') == 'measuring' else "screen_2",
                "message": result.get('message', ''),
                "timestamp": time.time()
            }
            await websocket.send_json(response)
            logger.info(f"[Phase {current_phase} - Response] - Phase change: {response}")

        elif result.get('status') == 'exercise_completed':
            # Exercise finished
            response = {
                "type": "exercise_completed",
                "final_scores": result.get('final_scores'),
                "timestamp": time.time()
            }
            await websocket.send_json(response)
            logger.info(f"[Phase scoring - Response] - Exercise completed: {response}")

        elif result.get('status') == 'processing':
            # Continue processing feedback
            if current_phase == 'detection':
                response = {
                    "type": "detection_feedback",
                    "stability_score": result.get('stability_score', 0.0),
                    "frames_stable": result.get('stability_counter', 0),
                    "required_stable_frames": 10,
                    "feedback_message": "Giữ nguyên tư thế..." if result.get('person_detected') else f"Không tìm thấy người trong khung hình"
                }
            elif current_phase == 'measuring':
                response = {
                    "type": "measuring_progress",
                    "captured": result.get('frames_captured', 0),
                    "total": result.get('total_required_frames', 100),
                    "progress_percentage": result.get('progress_percentage', 0),
                    "current_angles": result.get('current_angles', {})
                }
            elif current_phase == 'scoring':
                response = {
                    "type": "scoring_feedback",
                    "similarity_score": result.get('similarity_score', 0.0),
                    "scores": result.get('scores', {}),
                    "feedback_message": "Analyzing performance...",
                    "corrections": [],
                    "hold_progress": result.get('hold_progress', {}),
                    "pain_level": result.get('pain_level', 'unknown'),
                    "current_angles": result.get('current_angles', {})
                }
            await websocket.send_json(response)

    except Exception as e:
        logger.error(f"❌ [BACKEND] Frame processing error for session {session_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error_code": "FRAME_PROCESSING_FAILED",
            "message": "Failed to process frame"
        })







def _calculate_hold_progress(session: Dict[str, Any], is_correct_pose: bool) -> Dict[str, Any]:
    """Tính toán hold timer progress."""
    required_seconds = 5.0

    if is_correct_pose:
        if session.get("hold_start") is None:
            session["hold_start"] = time.time()

        elapsed = time.time() - session["hold_start"]
        if elapsed >= required_seconds:
            return {
                "holding": True,
                "current_seconds": elapsed,
                "required_seconds": required_seconds,
                "percentage": 100.0,
                "completed": True
            }
        else:
            return {
                "holding": True,
                "current_seconds": elapsed,
                "required_seconds": required_seconds,
                "percentage": (elapsed / required_seconds) * 100.0,
                "completed": False
            }
    else:
        session["hold_start"] = None
        return {
            "holding": False,
            "current_seconds": 0.0,
            "required_seconds": required_seconds,
            "percentage": 0.0,
            "completed": False
        }

async def _handle_phase_change_request(websocket: WebSocket, session_id: str, data: Dict[str, Any]):
    """Xử lý request chuyển phase thủ công."""
    # Check if session exists in service
    session_feedback = await pose_detection_service.get_session_feedback(session_id)
    if not session_feedback:
        await websocket.send_json({
            "type": "error",
            "error_code": "INVALID_SESSION",
            "message": "Session not found"
        })
        return

    current_phase = session_feedback.get("current_phase")
    target_phase = data.get("target_phase")

    # Validate phase transition
    valid_transitions = {
        "detection": ["measuring"],
        "measuring": ["scoring"],
        "scoring": []  # Cannot go back from scoring
    }

    if target_phase not in valid_transitions.get(current_phase, []):
        await websocket.send_json({
            "type": "error",
            "error_code": "PHASE_TRANSITION_INVALID",
            "message": f"Cannot transition from {current_phase} to {target_phase}"
        })
        return

    # For now, manual phase changes are not supported in service-centric architecture
    # This would require adding a method to the service
    await websocket.send_json({
        "type": "error",
        "error_code": "NOT_SUPPORTED",
        "message": "Manual phase changes are not currently supported"
    })

async def _handle_end_session(websocket: WebSocket, session_id: str, data: Dict[str, Any]):
    """Xử lý end session."""
    # Call service to end session
    end_response = await pose_detection_service.end_pose_session(session_id)

    if end_response.get('code') == '000':
        # Session ended successfully
        results = end_response.get('data', {}).get('results', {})
        if results:
            # Exercise was completed with results
            response = {
                "type": "exercise_completed",
                "final_scores": results,
                "timestamp": time.time()
            }
            logger.info(f"[Phase scoring - Response] - Exercise completed by user: {response}")
        else:
            # Session just ended without completion
            response = {
                "type": "session_ended",
                "message": "Session ended by user",
                "timestamp": time.time()
            }
            logger.info(f"Session {session_id}: Ended by user")
    else:
        # Error ending session
        response = {
            "type": "error",
            "error_code": "END_SESSION_FAILED",
            "message": end_response.get('message', 'Failed to end session')
        }
        logger.error(f"Failed to end session {session_id}: {end_response.get('message')}")

    await websocket.send_json(response)

@router.get("/session/{session_id}/results", response_model=DataResponse[PoseDetectionResultsResponse])
async def get_pose_results(
    session_id: str,
    current_user: User = Depends(login_required)
):
    """
    Retrieve final results of a completed pose detection session.

    This API returns comprehensive scoring and analysis results after session completion,
    including ROM scores, stability metrics, flow analysis, and personalized recommendations.

    **Authorization**: User must own the session.

    **Process**:
    1. Validates session ownership and completion status
    2. Retrieves or calculates final scoring results
    3. Returns structured analysis data

    **Response**: Complete session results with scoring breakdown.
    """
    # Get results from service
    try:
        results_response = await pose_detection_service.get_session_results(session_id)

        if results_response.get('code') != '000':
            if results_response.get('code') == '404':
                raise CustomException(
                    http_code=404,
                    code='404',
                    message="Pose detection session not found"
                )
            elif results_response.get('code') == '400':
                raise CustomException(
                    http_code=400,
                    code='400',
                    message=results_response.get('message', 'Session not completed yet')
                )
            else:
                raise CustomException(
                    http_code=500,
                    code='500',
                    message=results_response.get('message', 'Failed to get session results')
                )

        results = results_response.get('data', {})

        # Convert to proper response format if needed
        if not isinstance(results, PoseDetectionResultsResponse):
            # If results is a dict, wrap it in the response model
            duration = results.get('duration', 0)
            results_obj = PoseDetectionResultsResponse(
                overall_score=results.get('overall_score', 0),
                rom_scores=results.get('rom_scores', {}),
                stability_scores=results.get('stability_scores', {}),
                flow_scores=results.get('flow_scores', {}),
                symmetry_scores=results.get('symmetry_scores', {}),
                fatigue_level=results.get('fatigue_level', 'unknown'),
                recommendations=results.get('recommendations', []),
                duration=duration
            )
        else:
            results_obj = results

        logger.info(f"Retrieved results for session {session_id}")
        return DataResponse[PoseDetectionResultsResponse]().success_response(results_obj)

    except CustomException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for session {session_id}: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f"Failed to retrieve session results: {str(e)}"
        )

@router.post("/sync-motion")
async def sync_motion(
    session_id: str,
    reference_video: str,
    current_user: User = Depends(login_required)
):
    """
    Đồng bộ chuyển động với video tham khảo.

    So sánh chuyển động của user với video mẫu sử dụng DTW.
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Giả lập sync motion
        # Trong thực tế, sẽ load reference video và so sánh
        sync_result = {
            "sync_score": 78.5,
            "timing_score": 82.0,
            "accuracy_score": 75.0,
            "feedback": "Chuyển động hơi chậm so với mẫu, hãy tăng tốc độ"
        }

        return {
            "session_id": session_id,
            "sync_result": sync_result
        }

    except Exception as e:
        logger.error(f"Sync motion failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync motion failed: {str(e)}")

@router.post("/session/{session_id}/end", response_model=DataResponse[PoseDetectionSessionEndResponse])
async def end_pose_session(
    session_id: str,
    request: PoseDetectionSessionEndRequest,
    current_user: User = Depends(login_required)
):
    """
    End a pose detection session and retrieve final results.

    This API terminates an active session, performs final calculations if needed,
    and returns comprehensive session results including scoring and analysis.

    **Authorization**: User must own the session.

    **Process**:
    1. Validates session ownership and active status
    2. Performs final result calculations if session was in progress
    3. Cleans up session resources and logging
    4. Returns complete session summary

    **Response**: Final session results with completion metrics.
    """
    # Check if session exists via service
    session_feedback = await pose_detection_service.get_session_feedback(session_id)
    if not session_feedback:
        raise CustomException(
            http_code=404,
            code='404',
            message="Pose detection session not found"
        )

    # For now, skip user validation since service manages sessions
    # TODO: Add user validation to service methods

    try:
        # Call service to end session
        end_response = await pose_detection_service.end_pose_session(session_id)

        if end_response.get('code') != '000':
            if end_response.get('code') == '404':
                raise CustomException(
                    http_code=404,
                    code='404',
                    message="Pose detection session not found"
                )
            else:
                raise CustomException(
                    http_code=500,
                    code='500',
                    message=end_response.get('message', 'Failed to end session')
                )

        session_data = end_response.get('data', {})
        completion_score = session_data.get('completion_score', 0.0)
        duration_held = session_data.get('duration_held', 0.0)
        results = session_data.get('results', {})

        # Convert results to proper response format
        if isinstance(results, dict):
            results_obj = PoseDetectionResultsResponse(
                overall_score=results.get('overall_score', 0),
                rom_scores=results.get('rom_scores', {}),
                stability_scores=results.get('stability_scores', {}),
                flow_scores=results.get('flow_scores', {}),
                symmetry_scores=results.get('symmetry_scores', {}),
                fatigue_level=results.get('fatigue_level', 'unknown'),
                recommendations=results.get('recommendations', []),
                duration=results.get('duration', 0)
            )
        else:
            results_obj = results

        logger.info(f"Ended pose session {session_id} with completion score {completion_score}")

        response_data = PoseDetectionSessionEndResponse(
            session_id=session_id,
            task_id=request.task_id,
            completion_score=completion_score,
            duration_held=duration_held,
            results=results_obj
        )

        return DataResponse[PoseDetectionSessionEndResponse]().success_response(response_data)

    except CustomException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f"Failed to end pose detection session: {str(e)}"
        )

@router.get("/health", response_model=DataResponse[PoseDetectionHealthResponse])
async def pose_health_check():
    """
    Check pose detection service health and status.

    This API provides service availability information including MediaPipe status
    and current session load for monitoring and diagnostics.

    **Authorization**: No authentication required for health checks.

    **Process**:
    1. Checks MediaPipe module availability
    2. Counts active sessions from service
    3. Returns service status summary

    **Response**: Service health metrics and availability status.
    """
    # Get active sessions count from service
    try:
        active_sessions_count = await pose_detection_service.get_active_sessions_count()
    except Exception as e:
        logger.warning(f"Failed to get active sessions count: {str(e)}")
        active_sessions_count = 0

    health_data = PoseDetectionHealthResponse(
        status="healthy" if MEDIAPIPE_AVAILABLE else "degraded",
        mediapipe_available=MEDIAPIPE_AVAILABLE,
        active_sessions=active_sessions_count,
        version="1.0.0"
    )

    return DataResponse[PoseDetectionHealthResponse]().success_response(health_data)

# Task-specific endpoints for mobile app
class PoseSessionStartRequest(BaseModel):
    exercise_id: str
    stream_type: str = "websocket"

class PoseSessionStartResponse(BaseModel):
    code: str
    data: Dict[str, Any]

@task_router.post("/{task_id}/pose-session/start", response_model=PoseSessionStartResponse)
async def start_task_pose_session(
    task_id: str,
    request: PoseSessionStartRequest,
    current_user: User = Depends(login_required)
):
    """
    Khởi tạo session pose detection cho task cụ thể.

    Endpoint này match với expectation của mobile app.
    """
    try:
        # Map exercise_id to exercise_type for service
        exercise_type = map_exercise_id_to_type(request.exercise_id)

        # Call service to start session
        service_response = await pose_detection_service.start_pose_session(
            task_id=task_id,
            exercise_id=exercise_type,
            user_id=current_user.user_id,
            config={"exercise_type": exercise_type}
        )

        if service_response.get('code') != '000':
            raise CustomException(
                http_code=500,
                code='500',
                message=service_response.get('message', 'Failed to start pose detection session')
            )

        session_data = service_response.get('data', {})
        session_id = session_data.get('session_id')

        # Reference video URL (mock)
        reference_video_url = f"https://api.memotion.com/videos/{request.exercise_id}.mp4"

        logger.info(f"Started pose session {session_id} for task {task_id}, user {current_user.user_id}")

        return PoseSessionStartResponse(
            code="000",
            data={
                "session_id": session_id,
                "webrtc_offer": None,  # For WebRTC if needed
                "reference_video_url": reference_video_url
            }
        )

    except CustomException:
        raise
    except Exception as e:
        logger.error(f"Failed to start task pose session: {str(e)}")
        raise CustomException(
            http_code=500,
            code='500',
            message=f"Failed to start pose detection session: {str(e)}"
        )

# WebSocket endpoint for task-specific sessions
@task_router.websocket("/{task_id}/pose-feedback")
async def task_pose_feedback_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint cho real-time pose feedback theo task.

    Match với expectation của mobile app.
    """
    await websocket.accept()

    session_id = None

    try:
        # Wait for start_session message
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"error": "Timeout waiting for start_session"})
                await websocket.close()
                return

            if data.get("type") == "start_session":
                session_id = data.get("session_id")

                # Check if session exists in service
                session_feedback = await pose_detection_service.get_session_feedback(session_id)
                if not session_feedback:
                    await websocket.send_json({"error": "Invalid session_id"})
                    await websocket.close()
                    return

                # Check if session matches task
                if session_feedback.get("task_id") != task_id:
                    await websocket.send_json({"error": "Session does not match task"})
                    await websocket.close()
                    return

                logger.info(f"WebSocket connected for task {task_id}, session {session_id}")
                break
            else:
                await websocket.send_json({"error": "Expected start_session message first"})
                await websocket.close()
                return

        # Main processing loop
        while session_feedback.get("status") == "active":
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
                continue

            message_type = data.get("type")

            if message_type == "frame_data":
                frame_id = data.get("frame_id", 0)
                await _handle_task_frame_data(websocket, session_id, data)

            elif message_type == "end_session":
                await _handle_task_end_session(websocket, session_id, data)
                break

            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    "type": "error",
                    "error_code": "UNKNOWN_MESSAGE_TYPE",
                    "message": f"Unknown message type: {message_type}"
                })

            # Update session status
            session_feedback = await pose_detection_service.get_session_feedback(session_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {str(e)}")
        try:
            await websocket.send_json({"error": "Internal server error"})
        except:
            pass

async def _handle_task_frame_data(websocket: WebSocket, session_id: str, data: Dict[str, Any]):
    """Xử lý frame data từ mobile cho task WebSocket."""
    try:
        # Process frame through service
        result = await pose_detection_service.process_frame_stream(session_id, data)

        if result.get('code') != '000':
            await websocket.send_json({
                "type": "error",
                "error_code": result.get('code', 'UNKNOWN'),
                "message": result.get('message', 'Frame processing failed')
            })
            return

        feedback_data = result.get('data', {})

        # Send feedback to client
        await websocket.send_json({
            "type": "pose_feedback",
            "similarity_score": feedback_data.get('similarity_score', 0.0),
            "message": feedback_data.get('message', ''),
            "phase": feedback_data.get('phase', 'unknown'),
            "stability_score": feedback_data.get('stability_score', 0.0)
        })

    except Exception as e:
        logger.error(f"Error processing task frame data for session {session_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error_code": "FRAME_PROCESSING_ERROR",
            "message": "Failed to process frame data"
        })

async def _handle_task_end_session(websocket: WebSocket, session_id: str, data: Dict[str, Any]):
    """Xử lý end session request từ mobile cho task WebSocket."""
    try:
        # End session through service
        result = await pose_detection_service.end_pose_session(session_id)

        if result.get('code') != '000':
            await websocket.send_json({
                "type": "error",
                "error_code": result.get('code', 'UNKNOWN'),
                "message": result.get('message', 'Failed to end session')
            })
            return

        # Send completion message
        await websocket.send_json({
            "type": "session_ended",
            "message": "Session ended successfully"
        })

    except Exception as e:
        logger.error(f"Error ending task session {session_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error_code": "SESSION_END_ERROR",
            "message": "Failed to end session"
        })

def _calculate_hold_progress(session: Dict[str, Any], is_pose_correct: bool) -> Dict[str, Any]:
    """Tính toán tiến độ hold pose trong scoring phase."""
    required_seconds = 5.0  # Required hold time
    current_time = time.time()

    if is_pose_correct:
        if session.get("hold_start") is None:
            # Start holding
            session["hold_start"] = current_time
            return {
                "holding": True,
                "current_seconds": 0.0,
                "required_seconds": required_seconds,
                "percentage": 0.0,
                "completed": False
            }
        else:
            # Continue holding
            elapsed = current_time - session["hold_start"]
            if elapsed >= required_seconds:
                return {
                    "holding": True,
                    "current_seconds": elapsed,
                    "required_seconds": required_seconds,
                    "percentage": 100.0,
                    "completed": True
                }
            else:
                return {
                    "holding": True,
                    "current_seconds": elapsed,
                    "required_seconds": required_seconds,
                    "percentage": (elapsed / required_seconds) * 100.0,
                    "completed": False
                }
    else:
        # Reset hold timer if pose is not correct
        session["hold_start"] = None
        return {
            "holding": False,
            "current_seconds": 0.0,
            "required_seconds": required_seconds,
            "percentage": 0.0,
            "completed": False
        }

# Include task router into main router
router.include_router(task_router)
