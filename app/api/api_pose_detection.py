"""
Pose Detection API Routes for Memotion Backend

Provides REST endpoints and WebSocket support for real-time pose detection.
"""

import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from app.services.srv_exercise_library import ExerciseLibraryService
from app.services.srv_user import UserService
from app.models.model_user import User
from app.services.srv_pose_detection import pose_detection_service


logger = logging.getLogger(__name__)

router = APIRouter(tags=["pose-detection"])


class PoseSessionStartRequest(BaseModel):
    """Request model for starting pose detection session"""
    exercise_id: str
    stream_type: str = "webrtc"


class PoseSessionStartResponse(BaseModel):
    """Response model for pose session start"""
    code: str
    message: str
    data: Dict[str, Any] = None


@router.post("/{task_id}/pose-session/start", response_model=PoseSessionStartResponse)
async def start_pose_session(
    task_id: str,
    request: PoseSessionStartRequest,
    current_user: User = Depends(UserService.get_current_user),
    exercise_service: ExerciseLibraryService = Depends()
):
    """
    Start a new pose detection session for a task.

    Initializes WebRTC connection and prepares reference video.
    """
    logger.info(f"[API] Starting pose session for task {task_id}, exercise {request.exercise_id}")
    
    # Check if exercise is initialized, if not try to initialize it
    if request.exercise_id not in pose_detection_service.reference_videos:
        logger.info(f"[API] Exercise {request.exercise_id} not initialized, trying to initialize")
        try:
            # Get exercise details from database
            exercise = exercise_service.get_exercise_by_id(request.exercise_id)
            if exercise and exercise.video_path:
                # Convert URL path to file system path
                video_path = exercise.video_path.lstrip('/')
                logger.info(f"[API] Initializing exercise {request.exercise_id} with video path: {video_path}")
                success = await pose_detection_service.initialize_exercise(request.exercise_id, video_path)
                if success:
                    logger.info(f"[API] Successfully initialized exercise {request.exercise_id}")
                else:
                    logger.error(f"[API] Failed to initialize exercise {request.exercise_id}")
            else:
                logger.error(f"[API] Exercise {request.exercise_id} not found in database or no video path")
        except Exception as e:
            logger.error(f"[API] Error initializing exercise {request.exercise_id}: {e}")
    else:
        logger.info(f"[API] Exercise {request.exercise_id} already initialized")
    
    result = await pose_detection_service.start_pose_session(
        task_id=task_id,
        exercise_id=request.exercise_id
    )

    if result['code'] != '000':
        raise HTTPException(status_code=400, detail=result['message'])

    return PoseSessionStartResponse(**result)


@router.post("/{task_id}/pose-session/end")
async def end_pose_session(
    task_id: str,
    session_id: str,
    current_user: User = Depends(UserService.get_current_user)
):
    """
    End a pose detection session.
    """
    try:
        result = await pose_detection_service.end_pose_session(session_id)

        if result['code'] != '000':
            raise HTTPException(status_code=400, detail=result['message'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end pose session: {str(e)}")


@router.websocket("/{task_id}/pose-feedback")
async def pose_feedback_websocket(
    websocket: WebSocket,
    task_id: str
):
    """
    WebSocket endpoint for real-time pose detection feedback.

    Handles bidirectional communication for pose analysis:
    - Receives: session control messages
    - Sends: real-time feedback and session updates
    """
    await websocket.accept()

    session_id = None
    active_session = False

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get('type')

            if message_type == 'start_session':
                # Start new session
                session_id = data.get('session_id')
                exercise_id = data.get('exercise_id')

                if not session_id or not exercise_id:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'Missing session_id or exercise_id'
                    })
                    continue

                # Note: Session should already be started via REST API
                # This WebSocket connection maintains the feedback channel
                active_session = True

                await websocket.send_json({
                    'type': 'session_started',
                    'session_id': session_id,
                    'message': 'Pose detection session active'
                })

            elif message_type == 'frame_data':
                # Process frame data (in real implementation, this would come via WebRTC)
                if not active_session or not session_id:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'No active session'
                    })
                    continue

                # Log khi nhận frame từ mobile
                frame_id = data.get('frame_id', 0)
                logger.info(f"[POSE_REQUEST] Session {session_id}: Received frame {frame_id} from mobile")

                # In this simplified version, we expect frame_data as base64
                # In real WebRTC implementation, frames come through peer connection
                frame_data = data.get('frame_data')
                if not frame_data:
                    continue

                # Decode base64 frame data
                import base64
                try:
                    frame_bytes = base64.b64decode(frame_data)
                    logger.info(f"[WEBSOCKET] Session {session_id}: Received frame_data, decoded size: {len(frame_bytes)} bytes")
                except Exception as e:
                    await websocket.send_json({
                        'type': 'error',
                        'message': f'Invalid frame data: {str(e)}'
                    })
                    continue

                # Process frame
                result = await pose_detection_service.process_frame_stream(
                    session_id, frame_bytes
                )

                if result.get('status') == 'error':
                    logger.error(f"[WEBSOCKET] Session {session_id}: Processing failed: {result.get('error', 'Unknown error')}")
                    await websocket.send_json({
                        'type': 'error',
                        'message': result.get('error', 'Processing failed')
                    })
                    continue

                # Send feedback
                feedback_data = {
                    'type': 'pose_feedback',
                    'timestamp': result.get('timestamp', 0),
                    'frame_id': data.get('frame_id', 0),
                    'status': result['feedback']['status'],
                    'similarity_score': result['feedback']['similarity_score'],
                    'feedback': {
                        'message': result['feedback']['message'],
                        'corrections': result['feedback']['corrections']
                    },
                    'hold_progress': result['hold_progress'],
                    'session_info': result.get('session_info', {})
                }

                # Log kết quả so sánh chi tiết
                logger.info(f"[POSE_RESPONSE] Session {session_id}: Response sent - Status: {result['feedback']['status']}, "
                           f"Similarity: {result['feedback']['similarity_score']:.3f}, "
                           f"Message: '{result['feedback']['message']}', "
                           f"Hold Progress: {result['hold_progress']['percentage']:.1f}%, "
                           f"Corrections: {len(result['feedback']['corrections'])} items")

                await websocket.send_json(feedback_data)

                # Check for completion
                if result.get('completed', False):
                    completion_score = result['hold_progress'].get('percentage', 0) / 100.0
                    duration_held = result['hold_progress'].get('elapsed', 0)
                    
                    logger.info(f"[POSE_RESPONSE] Session {session_id}: Task completed - Score: {completion_score:.3f}, Duration: {duration_held:.2f}s")
                    
                    await websocket.send_json({
                        'type': 'task_completed',
                        'task_id': task_id,
                        'completion_score': completion_score,
                        'duration_held': duration_held
                    })

                    # End session
                    active_session = False

            elif message_type == 'end_session':
                # End session
                if session_id:
                    await pose_detection_service.end_pose_session(session_id)
                    active_session = False

                await websocket.send_json({
                    'type': 'session_ended',
                    'message': 'Pose detection session ended'
                })

            else:
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                })

    except WebSocketDisconnect:
        print(f"[WEBSOCKET] Client disconnected for task {task_id}")
        if session_id and active_session:
            await pose_detection_service.end_pose_session(session_id)

    except Exception as e:
        print(f"[WEBSOCKET] Error in pose feedback websocket: {str(e)}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': 'Internal server error'
            })
        except:
            pass  # WebSocket might already be closed


@router.get("/{task_id}/pose-session/{session_id}/status")
async def get_session_status(
    task_id: str,
    session_id: str,
    current_user: User = Depends(UserService.get_current_user)
):
    """
    Get current status of a pose detection session.
    """
    try:
        status = await pose_detection_service.get_session_feedback(session_id)

        if status is None:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            'code': '000',
            'message': 'Session status retrieved',
            'data': status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


# Background task for cleanup
@router.on_event("startup")
async def startup_event():
    """Initialize pose detection service on startup"""
    # Initialize common exercises (this would be done dynamically in production)
    # For demo purposes, we'll initialize some exercises with known video paths
    
    # Try to initialize exercises with available videos
    exercise_videos = {
        "arm_raise_exercise": "static/uploads/exercise/Exercise_7260756-hd_1920_1080_24fps_3.mp4",
        "elbow_flex_exercise": "static/uploads/exercise/Exercise_6970143-hd_1920_1080_30fps_2.mp4",
        "test_exercise": "static/uploads/exercise/Exercise_6970143-hd_1920_1080_30fps_1.mp4"
    }
    
    for exercise_id, video_path in exercise_videos.items():
        try:
            success = await pose_detection_service.initialize_exercise(exercise_id, video_path)
            if success:
                print(f"[STARTUP] Initialized exercise {exercise_id} with video {video_path}")
            else:
                print(f"[STARTUP] Failed to initialize exercise {exercise_id}")
        except Exception as e:
            print(f"[STARTUP] Error initializing exercise {exercise_id}: {e}")

    # Start cleanup task
    asyncio.create_task(cleanup_task())


async def cleanup_task():
    """Periodic cleanup of expired sessions"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        await pose_detection_service.cleanup_expired_sessions()