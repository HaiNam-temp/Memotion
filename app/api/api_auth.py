from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, BaseModel

from app.core.security import create_access_token
from app.helpers.exception_handler import CustomException
from app.schemas.sche_base import DataResponse
from app.schemas.sche_token import Token
from app.schemas.sche_user import UserItemResponse, UserRegisterRequest
from app.services.srv_user import UserService

router = APIRouter()

class LoginRequest(BaseModel):
    username: EmailStr = 'long.dh@teko.vn'
    password: str = 'secret123'

@router.post('/login', response_model=DataResponse[Token])
def login_access_token(form_data: LoginRequest, user_service: UserService = Depends()):
    user = user_service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail='Incorrect email or password')
    elif not user.is_active:
        raise HTTPException(status_code=401, detail='Inactive user')

    return DataResponse().success_response({
        'access_token': create_access_token(user_id=str(user.user_id))
    })

@router.post('/register', response_model=DataResponse[UserItemResponse])
def register(register_data: UserRegisterRequest, user_service: UserService = Depends()) -> Any:
    try:
        register_user = user_service.register_user(register_data)
        return DataResponse().success_response(data=register_user)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
