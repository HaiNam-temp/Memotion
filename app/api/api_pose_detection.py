"""
Pose Detection API Module for MEMOTION Backend.

Tích hợp MediaPipe pose detection vào FastAPI backend.
Expose APIs cho mobile app sử dụng.

CHIẾN LƯỢC GHÉP NỐI POSE DETECTION VỚI MOBILE APP
==================================================

1. TỔNG QUAN KIẾN TRÚC
----------------------
- Backend (FastAPI) + MediaPipe modules được merge thành một service duy nhất
- Mobile app giao tiếp qua REST API/WebSocket
- Docker container nhẹ chứa cả backend và pose detection

2. YÊU CẦU MERGE
---------------
2.1 Đồng nhất thư viện:
   - Backend: fastapi, sqlalchemy, alembic, uvicorn
   - MediaPipe: opencv-python, mediapipe, numpy, pillow
   - Chung: pydantic, typing, pathlib, asyncio

2.2 Docker tối ưu:
   - Base image: python:3.9-slim
   - Multi-stage build để giảm size
   - Chỉ copy cần thiết files
   - Volume mounts cho logs và data

2.3 Đồng bộ start:
   - Single entrypoint script khởi động cả FastAPI và MediaPipe services
   - Health checks đảm bảo cả hai components ready
   - Graceful shutdown cho cleanup resources

3. CHIẾN LƯỢC TÍCH HỢP
----------------------
3.1 API Endpoints:
   - POST /pose/start-session: Khởi tạo session với config
   - WebSocket /pose/stream: Real-time pose data streaming
   - POST /pose/calibrate: Calibration cho user
   - GET /pose/results/{session_id}: Lấy kết quả analysis
   - POST /pose/sync-motion: Sync với reference video

3.2 Data Flow:
   Mobile -> REST API -> MediaPipe Processor -> Analysis -> Response -> Mobile

3.3 Session Management:
   - Mỗi user có session riêng với unique ID
   - State persistence trong Redis/memory
   - Auto cleanup sau timeout

3.4 Error Handling:
   - Camera access errors
   - Network interruptions
   - Processing failures

4. TRIỂN KHAI DOCKER
--------------------
4.1 Dockerfile tối ưu:
   FROM python:3.9-slim as base
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   FROM base as builder
   COPY . .
   RUN pip install --no-cache-dir -e .

   FROM base as final
   COPY --from=builder /app /app
   EXPOSE 8000
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

4.2 Docker Compose:
   services:
     memotion-backend:
       build: .
       ports:
         - "8000:8000"
       volumes:
         - ./data:/app/data
         - ./logs:/app/logs
       environment:
         - POSE_DETECTION_ENABLED=true

5. MOBILE INTEGRATION
--------------------
5.1 API Client:
   - HTTP client cho REST calls
   - WebSocket client cho real-time data
   - Retry logic và error handling

5.2 Data Models:
   - PoseData: landmarks, angles, scores
   - SessionConfig: exercise type, duration
   - CalibrationData: joint limits

5.3 UI Integration:
   - Camera preview với overlay skeleton
   - Real-time feedback (scores, instructions)
   - Progress tracking

6. TESTING & MONITORING
-----------------------
6.1 Unit Tests:
   - Test MediaPipe functions
   - Test API endpoints
   - Test session management

6.2 Integration Tests:
   - End-to-end pose detection flow
   - Mobile app communication

6.3 Monitoring:
   - Health endpoints
   - Performance metrics
   - Error logging

7. TRIỂN KHAI PRODUCTION
-------------------------
7.1 Environment Variables:
   - CAMERA_DEVICE: camera source
   - POSE_MODEL_COMPLEXITY: model accuracy vs speed
   - SESSION_TIMEOUT: cleanup interval

7.2 Scaling:
   - Horizontal scaling với load balancer
   - GPU support cho MediaPipe nếu cần

7.3 Security:
   - API authentication
   - Input validation
   - Rate limiting
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

# Import từ mediapipe modules (sẽ được merge vào app)
try:
    # Giả sử mediapipe modules được copy vào app/mediapipe_modules/
    from app.mediapipe_modules.core import (
        VisionDetector, DetectorConfig, JointType, JOINT_DEFINITIONS,
        calculate_joint_angle, MotionPhase, SyncStatus, SyncState,
        MotionSyncController, create_arm_raise_exercise, create_elbow_flex_exercise,
        compute_single_joint_dtw, PoseLandmarkIndex,
    )
    from app.mediapipe_modules.modules import (
        VideoEngine, PlaybackState, PainDetector, PainLevel,
        HealthScorer, FatigueLevel, SafeMaxCalibrator, CalibrationState,
        UserProfile,
    )
    from app.mediapipe_modules.utils import (
        SessionLogger, put_vietnamese_text, draw_skeleton, draw_panel,
        draw_progress_bar, draw_phase_indicator, COLORS, draw_angle_arc,
        combine_frames_horizontal,
    )
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logging.warning("MediaPipe modules not available. Pose detection will be disabled.")

# Import auth dependencies
from app.helpers.login_manager import login_required
from app.models.model_user import User

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pose", tags=["pose-detection"])

# Session storage (in production, use Redis)
active_sessions = {}

class SessionConfig(BaseModel):
    """Cấu hình session pose detection cho mobile 2 màn hình."""
    exercise_type: str = "arm_raise"  # arm_raise, elbow_flex, etc.
    duration_minutes: int = 10
    camera_source: int = 0
    model_complexity: int = 1  # 0, 1, 2
    reference_video_path: Optional[str] = None  # Video mẫu để so sánh
    stability_threshold: float = 0.7  # Ngưỡng stability để chuyển phase
    min_measuring_frames: int = 100  # Số frame tối thiểu để measuring
    auto_phase_transition: bool = True  # Tự động chuyển phase

class PoseData(BaseModel):
    """Dữ liệu pose từ MediaPipe."""
    session_id: str
    timestamp: float
    landmarks: List[Dict[str, float]]
    angles: Dict[str, float]
    scores: Dict[str, float]
    phase: str
    feedback: str

class ResultsResponse(BaseModel):
    """Response kết quả analysis."""
    session_id: str
    total_score: float
    rom_scores: Dict[str, float]
    stability_scores: Dict[str, float]
    flow_scores: Dict[str, float]
    symmetry_scores: Dict[str, float]
    fatigue_level: str
    recommendations: List[str]

@router.post("/start-session", response_model=SessionResponse)
async def start_pose_session(
    config: SessionConfig,
    current_user: User = Depends(login_required)
):
    """
    Khởi tạo session pose detection mới.

    Tạo session với cấu hình tùy chỉnh cho user hiện tại.
    Session sẽ được lưu trong memory với timeout tự động cleanup.
    """
    if not MEDIAPIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pose detection service unavailable")

    try:
        session_id = str(uuid.uuid4())

        # Khởi tạo detector config
        detector_config = DetectorConfig(
            model_complexity=config.model_complexity,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Khởi tạo session logger
        session_logger = SessionLogger(session_id, Path(f"data/logs/{time.strftime('%Y%m%d')}"))

        # Khởi tạo detector
        detector = VisionDetector(detector_config)

        # Khởi tạo sync controller nếu có reference video
        sync_controller = None
        if config.reference_video_path:
            if config.exercise_type == "arm_raise":
                reference_exercise = create_arm_raise_exercise()
            elif config.exercise_type == "elbow_flex":
                reference_exercise = create_elbow_flex_exercise()
            else:
                reference_exercise = create_arm_raise_exercise()  # default

            sync_controller = MotionSyncController(reference_exercise)

        # Lưu session info với config mới
        active_sessions[session_id] = {
            "user_id": current_user.user_id,
            "config": config,
            "detector": detector,
            "sync_controller": sync_controller,
            "logger": session_logger,
            "start_time": time.time(),
            "status": "active",
            "current_phase": "detection",  # Bắt đầu với phase detection
            "stability_counter": 0,
            "measuring_frames": [],
            "scoring_started": False,
            "results": {}
        }

        logger.info(f"Started pose session {session_id} for user {current_user.user_id}")

        return SessionResponse(
            session_id=session_id,
            status="started",
            message="Pose detection session started successfully"
        )

    except Exception as e:
        logger.error(f"Failed to start pose session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@router.websocket("/stream/{session_id}")
async def pose_stream_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint cho real-time pose detection với logic mobile 2 màn hình.

    Logic xử lý theo yêu cầu mobile:
    Phase 1 (Màn hình 1): Detect user presence và stability
    - Nhận frame từ mobile qua WebRTC/WebSocket
    - Detect pose landmarks
    - Đánh giá stability (user đứng yên, pose rõ ràng)
    - Khi stable -> tự động chuyển Phase 2

    Phase 2 (Màn hình 1): Measuring cử động tự do
    - User cử động tự do
    - Thu thập data cử động
    - Khi đủ data -> tự động chuyển Phase 3

    Phase 3: Scoring với video mẫu
    - So sánh cử động với reference video
    - Tính điểm real-time
    - Trả feedback và kết quả
    """
    await websocket.accept()

    if session_id not in active_sessions:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    session = active_sessions[session_id]

    # Khởi tạo phase tracking
    current_phase = "detection"  # detection -> measuring -> scoring
    stability_counter = 0
    measuring_frames = []
    scoring_started = False

    try:
        while session["status"] == "active":
            # Nhận frame data từ mobile
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
            except asyncio.TimeoutError:
                # Timeout, gửi keepalive
                await websocket.send_json({"type": "keepalive"})
                continue

            if data.get("type") == "frame_data":
                frame_data = data.get("frame_data")  # base64 encoded frame
                frame_id = data.get("frame_id", 0)

                if not frame_data:
                    continue

                # Giả lập xử lý frame (thực tế sẽ dùng MediaPipe)
                # Phase 1: Detection & Stability
                if current_phase == "detection":
                    # Detect pose và đánh giá stability
                    stability_score = 0.8  # Giả lập từ MediaPipe

                    if stability_score > 0.7:
                        stability_counter += 1
                        if stability_counter >= 30:  # Stable trong 30 frames
                            current_phase = "measuring"
                            await websocket.send_json({
                                "type": "phase_change",
                                "phase": "measuring",
                                "message": "User detected and stable. Start measuring motion."
                            })
                            logger.info(f"Session {session_id}: Phase changed to measuring")
                    else:
                        stability_counter = max(0, stability_counter - 1)

                    # Gửi feedback cho mobile
                    await websocket.send_json({
                        "type": "detection_feedback",
                        "stability_score": stability_score,
                        "phase": current_phase
                    })

                # Phase 2: Measuring cử động tự do
                elif current_phase == "measuring":
                    # Thu thập cử động
                    measuring_frames.append({
                        "frame_id": frame_id,
                        "timestamp": time.time(),
                        "landmarks": [],  # Giả lập landmarks
                        "angles": {}      # Giả lập angles
                    })

                    # Kiểm tra đủ data để chuyển phase
                    if len(measuring_frames) >= 100:  # Đủ 100 frames
                        current_phase = "scoring"
                        await websocket.send_json({
                            "type": "phase_change",
                            "phase": "scoring",
                            "message": "Motion captured. Starting scoring with reference video."
                        })
                        logger.info(f"Session {session_id}: Phase changed to scoring")

                    # Gửi feedback measuring
                    await websocket.send_json({
                        "type": "measuring_feedback",
                        "frames_captured": len(measuring_frames),
                        "phase": current_phase
                    })

                # Phase 3: Scoring với video mẫu
                elif current_phase == "scoring":
                    if not scoring_started:
                        # Khởi tạo sync với reference video
                        scoring_started = True
                        logger.info(f"Session {session_id}: Started scoring phase")

                    # Giả lập scoring với reference video
                    similarity_score = 0.85  # DTW similarity
                    feedback_message = "Good form! Keep going."
                    corrections = ["Adjust elbow position"]

                    # Tính điểm chi tiết
                    rom_score = 88.0
                    stability_score = 92.0
                    flow_score = 85.0

                    # Gửi real-time scoring feedback
                    await websocket.send_json({
                        "type": "scoring_feedback",
                        "similarity_score": similarity_score,
                        "feedback_message": feedback_message,
                        "corrections": corrections,
                        "scores": {
                            "rom": rom_score,
                            "stability": stability_score,
                            "flow": flow_score
                        },
                        "phase": current_phase
                    })

                    # Kiểm tra hoàn thành (giả lập)
                    if len(measuring_frames) >= 200:  # Hoàn thành bài tập
                        # Tính kết quả cuối cùng
                        final_scores = {
                            "total_score": 87.5,
                            "rom_scores": {"left_shoulder": 90.0, "right_shoulder": 88.0},
                            "stability_scores": {"left_shoulder": 92.0, "right_shoulder": 89.0},
                            "flow_scores": {"left_shoulder": 88.0, "right_shoulder": 85.0},
                            "symmetry_scores": {"shoulder": 95.0},
                            "fatigue_level": "light",
                            "recommendations": ["Good job!", "Try to maintain form"]
                        }

                        await websocket.send_json({
                            "type": "exercise_completed",
                            "final_scores": final_scores
                        })

                        # Lưu kết quả vào session
                        session["results"] = final_scores
                        session["status"] = "completed"

                        logger.info(f"Session {session_id}: Exercise completed with score {final_scores['total_score']}")
                        break

            elif data.get("type") == "end_session":
                # User chủ động kết thúc
                session["status"] = "completed"
                await websocket.send_json({
                    "type": "session_ended",
                    "message": "Session ended by user"
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass

@router.get("/results/{session_id}", response_model=ResultsResponse)
async def get_pose_results(
    session_id: str,
    current_user: User = Depends(login_required)
):
    """
    Lấy kết quả analysis của session pose detection.

    Trả về các điểm số và khuyến nghị sau khi hoàn thành session.
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Giả lập kết quả analysis
        # Trong thực tế, sẽ tính toán từ dữ liệu đã thu thập
        results = {
            "total_score": 85.5,
            "rom_scores": {
                "left_shoulder": 90.0,
                "right_shoulder": 88.0,
                "left_elbow": 85.0,
                "right_elbow": 82.0
            },
            "stability_scores": {
                "left_shoulder": 92.0,
                "right_shoulder": 89.0,
                "left_elbow": 87.0,
                "right_elbow": 84.0
            },
            "flow_scores": {
                "left_shoulder": 88.0,
                "right_shoulder": 85.0,
                "left_elbow": 83.0,
                "right_elbow": 80.0
            },
            "symmetry_scores": {
                "shoulder": 95.0,
                "elbow": 90.0
            },
            "fatigue_level": "light",
            "recommendations": [
                "Tăng cường tập luyện vai trái",
                "Cải thiện độ ổn định khi giữ tư thế",
                "Nghỉ ngơi 5 phút giữa các set"
            ]
        }

        session["results"] = results

        return ResultsResponse(**results)

    except Exception as e:
        logger.error(f"Failed to get results for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

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

@router.delete("/session/{session_id}")
async def end_pose_session(
    session_id: str,
    current_user: User = Depends(login_required)
):
    """
    Kết thúc session pose detection.

    Cleanup resources và lưu kết quả cuối cùng.
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    if session["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Cleanup resources
        if "detector" in session:
            # Cleanup detector resources
            pass

        if "logger" in session:
            session["logger"].save_session()

        # Remove from active sessions
        del active_sessions[session_id]

        logger.info(f"Ended pose session {session_id}")

        return {"message": "Session ended successfully"}

    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

@router.get("/health")
async def pose_health_check():
    """
    Health check endpoint cho pose detection service.
    """
    return {
        "service": "pose-detection",
        "status": "healthy" if MEDIAPIPE_AVAILABLE else "unhealthy",
        "mediapipe_available": MEDIAPIPE_AVAILABLE,
        "active_sessions": len(active_sessions)
    }