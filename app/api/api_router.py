from fastapi import APIRouter

from app.api import api_user, api_auth, api_healthcheck, api_patient_profile, api_task

router = APIRouter()

router.include_router(api_healthcheck.router, tags=["health-check"], prefix="/healthcheck")
router.include_router(api_auth.router, tags=["authentication"], prefix="/auth")
router.include_router(api_user.router, tags=["user"], prefix="/users")
router.include_router(api_patient_profile.router, tags=["patient-profile"], prefix="/patient-profiles")
router.include_router(api_task.router, tags=["task"], prefix="/tasks")
