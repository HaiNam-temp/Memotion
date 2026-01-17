from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, BaseModel
from fastapi_sqlalchemy import db

from app.core.security import create_access_token
from app.helpers.exception_handler import CustomException
from app.schemas.sche_base import DataResponse
from app.schemas.sche_token import Token
from app.schemas.sche_user import UserItemResponse, UserRegisterRequest, UserRegisterV2Request
from app.services.srv_user import UserService

router = APIRouter()

class LoginRequest(BaseModel):
    username: EmailStr = 'long.dh@teko.vn'
    password: str = 'secret123'

@router.post('/login', response_model=DataResponse[Token])
def login_access_token(form_data: LoginRequest, user_service: UserService = Depends()) -> DataResponse[Token]:
    user = user_service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise CustomException(http_code=400, code='400', message='Incorrect email or password')
    elif not user.is_active:
        raise CustomException(http_code=400, code='400', message='Inactive user')

    # Update is_first_login to False if it's True
    if user.is_first_login:
        user.is_first_login = False
        db.session.commit()

    return DataResponse().success_response(data=Token(access_token=create_access_token(user_id=str(user.user_id))))

@router.post('/register', response_model=DataResponse)
def register(register_data: UserRegisterRequest, user_service: UserService = Depends()) -> Any:
    try:
        register_user = user_service.register_user(register_data)
        return DataResponse().success_response(data=register_user)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))

@router.post('/register/v2', response_model=DataResponse)
def register_v2(register_data: UserRegisterV2Request, user_service: UserService = Depends()) -> Any:
    """
    Register a new user (Version 2) - Simplified registration.
    
    This API allows simplified user registration with basic information.
    Creates a user account with no initial role assigned.
    User must update their role separately using the update role API.
    
    **Process**:
    1. Validate email and phone uniqueness
    2. Hash password and create user account with null role
    3. Return user information
    
    **Request Body**:
    - full_name: User's full name (required)
    - email: User's email address (required, unique)
    - password: User's password (required, min 6 characters)
    - phone: User's phone number (optional, unique if provided)
    
    **Response**: User registration information with null role.
    """
    try:
        register_user = user_service.register_user_v2(register_data)
        return DataResponse().success_response(data=register_user)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
