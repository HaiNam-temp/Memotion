import os
from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Settings(BaseSettings):
    PROJECT_NAME = os.getenv('PROJECT_NAME', 'FASTAPI BASE')
    SECRET_KEY = os.getenv('SECRET_KEY', '')
    API_PREFIX = '/api'
    BACKEND_CORS_ORIGINS = ['*']
    DATABASE_URL = os.getenv('SQL_DATABASE_URL', '')
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # Token expired after 7 days
    SECURITY_ALGORITHM = 'HS256'
    LOGGING_CONFIG_FILE = os.path.join(BASE_DIR, 'logging.ini')
    UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')

    # MediaPipe / Pose Detection settings
    MEDIAPIPE_MODELS_DIR = os.getenv(
        'MEDIAPIPE_MODELS_DIR', 
        os.path.join(BASE_DIR, 'app', 'mediapipe', 'mediapipe_be', 'models')
    )
    MEDIAPIPE_LOG_DIR = os.getenv(
        'MEDIAPIPE_LOG_DIR',
        os.path.join(BASE_DIR, 'app', 'mediapipe', 'mediapipe_be', 'data', 'logs')
    )
    POSE_SESSION_TIMEOUT = int(os.getenv('POSE_SESSION_TIMEOUT', '3600'))  # 1 hour default
    POSE_DETECTION_ENABLED = os.getenv('POSE_DETECTION_ENABLED', 'true').lower() == 'true'
    MEDIAPIPE_MODEL_COMPLEXITY = int(os.getenv('MEDIAPIPE_MODEL_COMPLEXITY', '1'))


settings = Settings()
