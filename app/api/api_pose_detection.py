"""
Pose Detection API - Real-time WebSocket Only.

Following Clean Architecture principles from PROJECT_STRUCTURE.md:
- Minimal HTTP endpoints for session management
- Real-time frame processing via WebSocket only
- NO REST frame processing endpoints

Author: MEMOTION Team
Version: 3.0.0 (Simplified Real-time Only)
"""

import logging
import time
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.helpers.exception_handler import CustomException
from app.schemas.sche_base import DataResponse
from app.schemas.sche_pose import (
    StartSessionRequest, StartSessionResponse,
    ProcessFrameRequest, ProcessFrameResponse,
    SessionResultsResponse, PoseHealthResponse
)
from app.services.srv_pose import pose_detection_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== HEALTH CHECK ====================

@router.get("/health", response_model=DataResponse[PoseHealthResponse])
def health_check() -> Any:
    """
    Check pose detection service health.
    
    Returns service status, MediaPipe availability, and active sessions count.
    """
    try:
        health = pose_detection_service.get_health()
        return DataResponse().success_response(data=health)
    except Exception as e:
        logger.error(f"health_check error: {str(e)}", exc_info=True)
        raise CustomException(http_code=500, code='500', message=str(e))


@router.get("/ws-stats")
def get_websocket_stats() -> Any:
    """
    Get WebSocket connection statistics.
    
    Returns real-time WebSocket connection stats including total connections
    and connections per session.
    """
    from app.services.ws_manager import ws_connection_manager
    
    try:
        ws_stats = ws_connection_manager.get_stats()
        return DataResponse().success_response(data=ws_stats)
    except Exception as e:
        logger.error(f"get_websocket_stats error: {str(e)}", exc_info=True)
        raise CustomException(http_code=500, code='500', message=str(e))


# ==================== SESSION MANAGEMENT ====================

@router.post("/sessions", response_model=DataResponse[StartSessionResponse])
def start_session(request: StartSessionRequest) -> Any:
    """
    Start a new pose detection session.
    
    Creates a new MemotionEngine instance and returns session_id + websocket_url.
    Client should connect to websocket_url for real-time frame streaming.
    
    **Response**: Session ID and WebSocket URL for real-time streaming.
    """
    logger.info(f"start_session request: user_id={request.user_id}, exercise={request.exercise_type}")
    
    try:
        response = pose_detection_service.start_session(request)
        logger.info(f"start_session success: session_id={response.session_id}, ws_url={response.websocket_url}")
        return DataResponse().success_response(data=response)
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"start_session error: {str(e)}", exc_info=True)
        raise CustomException(http_code=500, code='500', message=str(e))


@router.delete("/sessions/{session_id}", response_model=DataResponse[SessionResultsResponse])
def end_session(session_id: str) -> Any:
    """
    End a pose detection session and retrieve final results.
    
    Terminates the session, calculates final scores, and returns
    comprehensive results including ROM, stability, flow scores,
    and recommendations.
    
    **Response**: Final session results with scores and recommendations.
    """
    logger.info(f"end_session request: session_id={session_id}")
    
    try:
        response = pose_detection_service.end_session(session_id)
        logger.info(f"end_session success: session_id={session_id}, total_score={response.total_score}")
        return DataResponse().success_response(data=response)
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"end_session error: {str(e)}", exc_info=True)
        raise CustomException(http_code=500, code='500', message=str(e))


# ==================== WEBSOCKET REAL-TIME STREAMING ====================

@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time pose detection streaming.
    
    **Flow**:
    1. POST /sessions → get session_id + websocket_url
    2. Connect to this WebSocket endpoint
    3. Stream frames, receive results in real-time
    4. DELETE /sessions/{id} → get final results
    
    **Protocol**:
    - Client sends: {"frame_data": "<base64>", "timestamp_ms": 1234}
    - Server sends: {"phase": 1, "phase_name": "detection", "data": {...}, "fps": 30}
    
    **Performance**:
    - Latency: ~10-30ms per frame
    - Recommended: 30fps
    """
    from app.services.ws_manager import ws_connection_manager
    
    logger.info(f"websocket_endpoint: Connection request for session_id={session_id}")
    
    # Validate session before accepting
    try:
        session = pose_detection_service.get_session(session_id)
    except CustomException as e:
        logger.warning(f"websocket_endpoint: Session not found: {session_id}")
        await websocket.close(code=4004, reason=str(e.message))
        return
    
    # Register connection
    try:
        connection = await ws_connection_manager.connect(
            websocket=websocket,
            session_id=session_id,
            user_id=session.user_id
        )
    except Exception as e:
        logger.error(f"websocket_endpoint: Failed to register connection: {e}")
        return
    
    logger.info(f"websocket_endpoint: Connected session_id={session_id}")
    
    # Frame processing metrics
    frame_count = 0
    start_time = time.time()
    last_fps_calc = start_time
    current_fps = 0.0
    
    try:
        while True:
            # Receive frame data
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON format", "code": "400"})
                continue
            
            # Validate required fields
            if 'frame_data' not in data:
                await websocket.send_json({"error": "Missing field: frame_data", "code": "400"})
                continue
            
            # Get timestamp
            timestamp_ms = data.get('timestamp_ms', int(time.time() * 1000))
            
            # Create request and process
            request = ProcessFrameRequest(
                session_id=session_id,
                frame_data=data['frame_data'],
                timestamp_ms=timestamp_ms
            )
            
            try:
                response = pose_detection_service.process_frame(request)
                frame_count += 1
                
                # Calculate FPS every second
                current_time = time.time()
                if current_time - last_fps_calc >= 1.0:
                    current_fps = frame_count / (current_time - start_time)
                    last_fps_calc = current_time
                
                # Send response
                await websocket.send_json({
                    "phase": response.phase,
                    "phase_name": response.phase_name,
                    "data": response.data,
                    "message": response.message,
                    "warning": response.warning,
                    "timestamp": response.timestamp,
                    "frame_number": frame_count,
                    "fps": round(current_fps, 1)
                })
                
                # Check if session completed
                if response.phase_name == "completed":
                    logger.info(f"websocket_endpoint: Session completed: {session_id}")
                    await websocket.send_json({
                        "event": "session_completed",
                        "message": "Call DELETE /sessions/{id} for final results."
                    })
                    
            except CustomException as e:
                await websocket.send_json({"error": e.message, "code": e.code})
            except Exception as e:
                logger.error(f"websocket_endpoint: Processing error: {e}", exc_info=True)
                await websocket.send_json({"error": f"Processing failed: {str(e)}", "code": "500"})
                
    except WebSocketDisconnect:
        logger.info(f"websocket_endpoint: Disconnected session_id={session_id}, frames={frame_count}")
    except Exception as e:
        logger.error(f"websocket_endpoint error: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        await ws_connection_manager.disconnect(websocket, session_id)
        logger.info(f"websocket_endpoint: Cleanup completed: session_id={session_id}")
