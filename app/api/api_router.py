from fastapi import APIRouter

from app.api import api_user, api_auth, api_healthcheck

router = APIRouter()

router.include_router(api_healthcheck.router, tags=["health-check"], prefix="/healthcheck")
router.include_router(api_auth.router, tags=["authentication"], prefix="/auth")
router.include_router(api_user.router, tags=["user"], prefix="/users")
