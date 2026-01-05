import os
import shutil
import uuid
from typing import Any
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.schemas.sche_base import DataResponse
from app.helpers.exception_handler import CustomException

router = APIRouter()

ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'video': {'mp4', 'mov', 'avi', 'mkv'}
}

def validate_file_extension(filename: str) -> str:
    ext = filename.split('.')[-1].lower()
    if ext in ALLOWED_EXTENSIONS['image']:
        return 'image'
    if ext in ALLOWED_EXTENSIONS['video']:
        return 'video'
    return None

@router.post("", response_model=DataResponse[str])
async def upload_file(file: UploadFile = File(...)) -> Any:
    try:
        file_type = validate_file_extension(file.filename)
        if not file_type:
            raise CustomException(http_code=400, code='400', message="File type not allowed. Only images and videos are supported.")

        # Create upload directory if not exists
        upload_path = os.path.join(settings.UPLOAD_DIR, file_type + 's')
        os.makedirs(upload_path, exist_ok=True)

        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_location = os.path.join(upload_path, unique_filename)

        # Save file
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return relative path
        relative_path = f"/static/uploads/{file_type}s/{unique_filename}"
        
        return DataResponse().success_response(data=relative_path)

    except CustomException as e:
        raise e
    except Exception as e:
        raise CustomException(http_code=500, code='500', message=str(e))
