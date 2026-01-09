import os
import shutil
import json
from typing import Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.core.config import settings, BASE_DIR
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

def load_counter():
    counter_file = os.path.join(BASE_DIR, 'counter.json')
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as f:
            return json.load(f)
    return {"nutri": 0, "exer": 0, "medical": 0}

def save_counter(counter):
    counter_file = os.path.join(BASE_DIR, 'counter.json')
    with open(counter_file, 'w') as f:
        json.dump(counter, f)

@router.post("", response_model=DataResponse[str])
async def upload_file(file: UploadFile = File(...), type: str = Form(...)) -> Any:
    try:
        if type not in ["medication", "nutrition", "exercise"]:
            raise CustomException(http_code=400, code='400', message="Invalid type. Must be medication, nutrition, or exercise.")

        counter = load_counter()
        num = counter[type]
        counter[type] = num + 1
        save_counter(counter)

        file_type = validate_file_extension(file.filename)
        if not file_type:
            raise CustomException(http_code=400, code='400', message="File type not allowed. Only images and videos are supported.")

        # Create upload directory if not exists
        upload_path = os.path.join(settings.UPLOAD_DIR, type)
        os.makedirs(upload_path, exist_ok=True)

        # Generate new filename
        file_extension = file.filename.split('.')[-1].lower()
        original_name = file.filename.rsplit('.', 1)[0]
        new_filename = f"{type.capitalize()}_{original_name}_{num}.{file_extension}"
        file_location = os.path.join(upload_path, new_filename)

        # Save file
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return relative path
        relative_path = f"/static/uploads/{type}/{new_filename}"
        
        return DataResponse().success_response(data=relative_path)

    except CustomException as e:
        raise e
    except Exception as e:
        raise CustomException(http_code=500, code='500', message=str(e))
