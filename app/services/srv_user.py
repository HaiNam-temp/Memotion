import jwt
import logging
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi_sqlalchemy import db
from pydantic import ValidationError
from starlette import status

from app.models.model_user import User
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.schemas.sche_token import TokenPayload
from app.schemas.sche_user import UserCreateRequest, UserUpdateMeRequest, UserUpdateRequest, UserRegisterRequest
from app.repository.repo_user import UserRepository
from app.helpers.enums import UserRole

from app.helpers.exception_handler import CustomException

logger = logging.getLogger(__name__)

reusable_oauth2 = HTTPBearer(
    scheme_name='Authorization'
)

class UserService:
    def __init__(self, user_repo: UserRepository = Depends()):
        self.user_repo = user_repo

    def get_users(self):
        return self.user_repo.get_all()

    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def get_current_user(http_authorization_credentials=Depends(reusable_oauth2)) -> User:
        try:
            payload = jwt.decode(
                http_authorization_credentials.credentials, settings.SECRET_KEY,
                algorithms=[settings.SECURITY_ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (jwt.PyJWTError, ValidationError) as e:
            logger.error(f"Credential validation failed: {e}")
            raise CustomException(
                http_code=status.HTTP_403_FORBIDDEN,
                code='403',
                message="Could not validate credentials"
            )
        # Note: Ideally we should use UserRepository here too, but for static dependency it's harder.
        # We can use db.session directly or refactor to use a class dependency.
        # For now, direct query is acceptable for this helper.
        user = db.session.query(User).filter(User.user_id == token_data.user_id).first()
        if not user:
            logger.error(f"User not found: {token_data.user_id}")
            raise CustomException(http_code=404, code='404', message="User not found")
        
        logger.info(f"User authenticated: {user.email}")
        return user

    def register_user(self, data: UserRegisterRequest):
        if self.user_repo.get_by_email(data.email):
            raise Exception('Email already exists')
        
        if data.phone and self.user_repo.get_by_phone(data.phone):
            raise Exception('Phone number already exists')
        
        hashed_password = get_password_hash(data.password)
        new_user = User(
            full_name=data.full_name,
            email=data.email,
            hashed_password=hashed_password,
            phone=data.phone,
            is_active=True,
            role=data.role.value,
        )
        created_user = self.user_repo.create(new_user)

        if data.role == UserRole.CARETAKER:
            # Validate patient info
            if not data.patient_email or not data.patient_full_name:
                raise Exception('Patient email and full name are required for Caretaker registration')

            # Create linked Patient account
            patient_email = data.patient_email
            
            # Check if patient email exists
            if self.user_repo.get_by_email(patient_email):
                 raise Exception(f'Patient account {patient_email} already exists')

            if data.patient_phone and self.user_repo.get_by_phone(data.patient_phone):
                 raise Exception(f'Patient phone number {data.patient_phone} already exists')

            patient_user = User(
                full_name=data.patient_full_name,
                email=patient_email,
                hashed_password=hashed_password, # Same password as caretaker
                phone=data.patient_phone,
                is_active=True,
                role=UserRole.PATIENT.value
            )
            created_patient = self.user_repo.create(patient_user)
            
            # Create relationship
            self.user_repo.create_patient_caretaker(
                patient_id=created_patient.user_id,
                caretaker_id=created_user.user_id
            )
            
            # Attach patient info for response
            created_user.patient = created_patient

        return created_user

    def update_me(self, data: UserUpdateMeRequest, current_user: User):
        if data.email is not None:
            exist_user = self.user_repo.get_by_email(data.email)
            if exist_user and exist_user.user_id != current_user.user_id:
                raise Exception('Email already exists')
        
        current_user.full_name = current_user.full_name if data.full_name is None else data.full_name
        current_user.email = current_user.email if data.email is None else data.email
        if data.password:
            current_user.hashed_password = get_password_hash(data.password)
            
        return self.user_repo.update(current_user)

    def get(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise Exception('User not exists')
        return user

