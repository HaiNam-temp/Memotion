from fastapi import APIRouter

from app.api import api_user, api_auth, api_healthcheck, api_patient_profile, api_task, api_upload, api_nutrition_library, api_medication_library, api_exercise_library, api_notification, api_care_plan, api_pose_detection

router = APIRouter()

router.include_router(api_healthcheck.router, tags=["health-check"], prefix="/healthcheck")
router.include_router(api_auth.router, tags=["authentication"], prefix="/auth")
router.include_router(api_user.router, tags=["user"], prefix="/users")
router.include_router(api_patient_profile.router, tags=["patient-profile"], prefix="/patient-profiles")
router.include_router(api_care_plan.router, tags=["ai-care-plan"], prefix="/care-plans")
router.include_router(api_task.router, tags=["task"], prefix="/tasks")
router.include_router(api_upload.router, tags=["upload"], prefix="/upload")
router.include_router(api_nutrition_library.router, tags=["nutrition-library"], prefix="/nutrition-library")
router.include_router(api_medication_library.router, tags=["medication-library"], prefix="/medication-library")
router.include_router(api_exercise_library.router, tags=["exercise-library"], prefix="/exercise-library")
router.include_router(api_notification.router, tags=["notification"], prefix="/notifications")
router.include_router(api_pose_detection.router, tags=["pose-detection"], prefix="/api")
