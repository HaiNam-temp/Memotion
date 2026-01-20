"""
Vision Detector Module for MEMOTION.

Sử dụng MediaPipe Tasks API (phiên bản mới nhất) để detect
Pose và Face landmarks từ video/camera input.

Author: MEMOTION Team
Version: 1.0.0
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision as mp_vision
except ImportError as e:
    raise ImportError(
        "MediaPipe not found. Install with: pip install mediapipe"
    ) from e

from .data_types import (
    DetectionResult,
)


@dataclass
class DetectorConfig:
    """
    Cấu hình cho VisionDetector.
    
    Attributes:
        pose_model_path: Đường dẫn đến file pose_landmarker.task.
        face_model_path: Đường dẫn đến file face_landmarker.task.
        min_pose_detection_confidence: Ngưỡng tin cậy pose detection.
        min_pose_tracking_confidence: Ngưỡng tin cậy pose tracking.
        min_face_detection_confidence: Ngưỡng tin cậy face detection.
        min_face_tracking_confidence: Ngưỡng tin cậy face tracking.
        num_poses: Số lượng người tối đa detect.
        num_faces: Số lượng khuôn mặt tối đa detect.
        running_mode: Chế độ chạy (IMAGE, VIDEO, LIVE_STREAM).
    """
    pose_model_path: Optional[str] = "app/mediapipe_models/pose_landmarker_lite.task"
    face_model_path: Optional[str] = None
    min_pose_detection_confidence: float = 0.5
    min_pose_tracking_confidence: float = 0.5
    min_face_detection_confidence: float = 0.5
    min_face_tracking_confidence: float = 0.5
    num_poses: int = 1
    num_faces: int = 1
    running_mode: str = "VIDEO"  # IMAGE, VIDEO, LIVE_STREAM


class VisionDetector:
    """
    Wrapper class cho MediaPipe Tasks API.
    
    Cung cấp interface thống nhất để detect Pose và Face landmarks
    từ ảnh hoặc video frames.
    
    Example:
        >>> config = DetectorConfig(pose_model_path="pose_landmarker.task")
        >>> detector = VisionDetector(config)
        >>> result = detector.process_frame(frame, timestamp_ms=0)
        >>> if result.has_pose():
        ...     pose_array = result.pose_landmarks.to_numpy()
    """
    
    def __init__(self, config: DetectorConfig):
        """
        Khởi tạo VisionDetector.
        
        Args:
            config: Cấu hình detector.
            
        Raises:
            FileNotFoundError: Nếu model file không tồn tại.
            RuntimeError: Nếu không thể khởi tạo MediaPipe.
        """
        self._config = config
        self._pose_landmarker: Optional[mp_vision.PoseLandmarker] = None
        self._face_landmarker: Optional[mp_vision.FaceLandmarker] = None
        self._frame_count = 0
        
        self._init_pose_landmarker()
        self._init_face_landmarker()
    
    def _get_running_mode(self) -> mp_vision.RunningMode:
        """Chuyển đổi string running mode sang enum."""
        mode_map = {
            "IMAGE": mp_vision.RunningMode.IMAGE,
            "VIDEO": mp_vision.RunningMode.VIDEO,
            "LIVE_STREAM": mp_vision.RunningMode.LIVE_STREAM,
        }
        return mode_map.get(
            self._config.running_mode.upper(),
            mp_vision.RunningMode.VIDEO
        )
    
    def _init_pose_landmarker(self) -> None:
        """Khởi tạo Pose Landmarker với built-in model."""
        base_options = mp_tasks.BaseOptions()  # Use built-in model
        if self._config.pose_model_path is not None:
            model_path = Path(self._config.pose_model_path)
            if model_path.exists():
                base_options = mp_tasks.BaseOptions(
                    model_asset_path=str(model_path)
                )
            else:
                print(f"Warning: Pose model not found: {self._config.pose_model_path}, using built-in model")
        
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=self._get_running_mode(),
            num_poses=self._config.num_poses,
            min_pose_detection_confidence=self._config.min_pose_detection_confidence,
            min_pose_presence_confidence=self._config.min_pose_tracking_confidence,
            min_tracking_confidence=self._config.min_pose_tracking_confidence,
            output_segmentation_masks=False,
        )
        
        self._pose_landmarker = mp_vision.PoseLandmarker.create_from_options(options)
        
        self._pose_landmarker = mp_vision.PoseLandmarker.create_from_options(options)
    
    def _init_face_landmarker(self) -> None:
        """Khởi tạo Face Landmarker nếu có model path."""
        if self._config.face_model_path is None:
            return
            
        model_path = Path(self._config.face_model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Face model not found: {self._config.face_model_path}"
            )
        
        base_options = mp_tasks.BaseOptions(
            model_asset_path=str(model_path)
        )
        
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=self._get_running_mode(),
            num_faces=self._config.num_faces,
            min_face_detection_confidence=self._config.min_face_detection_confidence,
            min_face_presence_confidence=self._config.min_face_tracking_confidence,
            min_tracking_confidence=self._config.min_face_tracking_confidence,
            output_face_blendshapes=True,  # Cho FACS analysis sau này
            output_facial_transformation_matrixes=False,
        )
        
        self._face_landmarker = mp_vision.FaceLandmarker.create_from_options(options)
    

    
    def process_frame(
        self,
        image: np.ndarray,
        timestamp_ms: Optional[int] = None
    ) -> DetectionResult:
        """
        Xử lý một frame ảnh và trả về detection results.
        
        Args:
            image: Ảnh BGR từ OpenCV, shape (H, W, 3).
            timestamp_ms: Timestamp tính bằng milliseconds.
                         Nếu None, sẽ tự động tính từ frame count.
        
        Returns:
            DetectionResult chứa pose và face landmarks.
            
        Note:
            - Ảnh đầu vào phải ở định dạng BGR (từ OpenCV).
            - Landmarks trả về là normalized coordinates (0-1).
            - World landmarks có đơn vị meters với gốc tại hip center.
        """
        if image is None or image.size == 0:
            return DetectionResult()
        
        # Auto timestamp nếu không được cung cấp
        if timestamp_ms is None:
            timestamp_ms = int(self._frame_count * (1000 / 30))  # Giả sử 30 FPS
        self._frame_count += 1
        
        frame_height, frame_width = image.shape[:2]
        
        # Convert BGR to RGB cho MediaPipe
        image_rgb = image[:, :, ::-1].copy()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        result = DetectionResult(
            timestamp_ms=timestamp_ms,
        )
        
        # Process Pose
        if self._pose_landmarker is not None:
            try:
                pose_result = self._pose_landmarker.detect_for_video(
                    mp_image, timestamp_ms
                )
                
                if pose_result.pose_landmarks and len(pose_result.pose_landmarks) > 0:
                    result.pose_landmarks = pose_result.pose_landmarks[0]
                    
                    # World landmarks (real-world 3D coordinates)
                    if pose_result.pose_world_landmarks and len(pose_result.pose_world_landmarks) > 0:
                        result.pose_world_landmarks = pose_result.pose_world_landmarks[0]
            except Exception as e:
                print(f"Pose detection error: {str(e)}")
        
        # Process Face
        if self._face_landmarker is not None:
            try:
                face_result = self._face_landmarker.detect_for_video(
                    mp_image, timestamp_ms
                )
                
                if face_result.face_landmarks and len(face_result.face_landmarks) > 0:
                    result.face_landmarks = face_result.face_landmarks[0]
            except Exception as e:
                print(f"Face detection error: {str(e)}")
        
        return result
    
    def process_image(self, image: np.ndarray) -> DetectionResult:
        """
        Xử lý một ảnh tĩnh (không phải video frame).
        
        Sử dụng cho trường hợp IMAGE running mode.
        
        Args:
            image: Ảnh BGR từ OpenCV.
            
        Returns:
            DetectionResult chứa landmarks.
        """
        if image is None or image.size == 0:
            return DetectionResult()
        
        frame_height, frame_width = image.shape[:2]
        
        image_rgb = image[:, :, ::-1].copy()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        result = DetectionResult(
            timestamp_ms=0,
        )
        
        if self._pose_landmarker is not None:
            try:
                pose_result = self._pose_landmarker.detect(mp_image)
                
                if pose_result.pose_landmarks and len(pose_result.pose_landmarks) > 0:
                    result.pose_landmarks = pose_result.pose_landmarks[0]
                    
                    if pose_result.pose_world_landmarks and len(pose_result.pose_world_landmarks) > 0:
                        result.pose_world_landmarks = pose_result.pose_world_landmarks[0]
            except Exception as e:
                print(f"Pose detection error: {str(e)}")
        
        if self._face_landmarker is not None:
            try:
                face_result = self._face_landmarker.detect(mp_image)
                
                if face_result.face_landmarks and len(face_result.face_landmarks) > 0:
                    result.face_landmarks = face_result.face_landmarks[0]
            except Exception as e:
                print(f"Face detection error: {str(e)}")
        
        return result
    
    def reset(self) -> None:
        """Reset frame counter và internal state."""
        self._frame_count = 0
    
    def close(self) -> None:
        """Giải phóng tài nguyên."""
        if self._pose_landmarker is not None:
            self._pose_landmarker.close()
            self._pose_landmarker = None
            
        if self._face_landmarker is not None:
            self._face_landmarker.close()
            self._face_landmarker = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False