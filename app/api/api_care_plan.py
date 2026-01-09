"""
Care Plan API endpoints.
Handles HTTP requests for AI-powered care plan generation and management.
"""
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.srv_care_plan import CarePlanService
from app.services.srv_user import UserService
from app.models.model_user import User
from app.schemas.sche_base import DataResponse
from app.schemas.sche_care_plan import (
    CarePlanGenerationRequest,
    CarePlanGenerationResponse,
    CarePlanUpdateResponse,
    CarePlanSummaryResponse,
    TaskRefinementRequest,
    TaskRefinementResponse,
    CarePlanDeletionResponse
)
from app.helpers.login_manager import login_required
from app.helpers.exception_handler import CustomException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/generate', response_model=DataResponse[CarePlanGenerationResponse])
def generate_care_plan(
    request: CarePlanGenerationRequest,
    care_plan_service: CarePlanService = Depends(),
    current_user: User = Depends(login_required)
) -> DataResponse[CarePlanGenerationResponse]:
    """
    Generate AI-powered care plan for patient.
    
    **Authorization**: CARETAKER role required.
    
    **Process**:
    1. Validates caretaker has assigned patient
    2. Loads patient profile and therapy details
    3. Calls Gemini AI to generate personalized care plan
    4. Creates care_plan and task records in database
    
    **Response**: Care plan summary with task count and recommendations.
    """
    try:
        logger.info(f"generate_care_plan request from user {current_user.user_id}")
        
        result = care_plan_service.generate_care_plan_by_caretaker(
            current_user=current_user,
            plan_duration_days=request.plan_duration_days,
            regenerate=request.regenerate
        )
        
        logger.info(f"generate_care_plan success: {result.get('total_tasks')} tasks created")
        return DataResponse().success_response(data=result)
        
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"generate_care_plan error: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f'Failed to generate care plan: {str(e)}'
        )


class UpdateCarePlanRequest(BaseModel):
    """Request schema for updating care plan."""
    plan_duration_days: int = Field(default=7, ge=1, le=30, description="Duration of updated care plan in days")


@router.post('/update', response_model=DataResponse[CarePlanUpdateResponse])
def update_care_plan(
    request: Optional[CarePlanGenerationRequest] = None,
    care_plan_service: CarePlanService = Depends(),
    current_user: User = Depends(login_required)
) -> DataResponse[CarePlanUpdateResponse]:
    """
    Update existing care plan with new tasks based on current patient profile.
    
    **Authorization**: CARETAKER role required.
    
    **Process**:
    1. Validates caretaker has assigned patient with existing care plan
    2. Loads updated patient profile and therapy details
    3. Calls Gemini AI to generate updated personalized care plan
    4. Deletes existing tasks and creates new task records in database
    
    **Response**: Updated care plan summary with task count and recommendations.
    """
    try:
        logger.info(f"update_care_plan request from user {current_user.user_id}")
        
        if request is None:
            request = UpdateCarePlanRequest()
        
        result = care_plan_service.update_care_plan_by_caretaker(
            current_user=current_user,
            plan_duration_days=request.plan_duration_days
        )
        
        logger.info(f"update_care_plan success: {result.get('total_tasks')} tasks updated")
        return DataResponse().success_response(data=result)
        
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"update_care_plan error: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f'Failed to update care plan: {str(e)}'
        )


@router.get('/summary', response_model=DataResponse[CarePlanSummaryResponse])
def get_care_plan_summary(
    care_plan_service: CarePlanService = Depends(),
    current_user: User = Depends(login_required)
) -> DataResponse[CarePlanSummaryResponse]:
    """
    Get care plan summary for current user.
    
    **Authorization**: PATIENT or CARETAKER role.
    
    **For Patient**: Returns their own care plan summary.
    **For Caretaker**: Returns care plan of assigned patient.
    
    **Response**: Care plan details with task statistics.
    """
    try:
        from app.helpers.enums import UserRole
        from app.repository.repo_user import UserRepository
        
        logger.info(f"get_care_plan_summary request from user {current_user.user_id}")
        
        # Determine patient_id based on role
        if current_user.role == UserRole.PATIENT.value:
            patient_id = current_user.user_id
        elif current_user.role == UserRole.CARETAKER.value:
            user_repo = UserRepository()
            patient_id = user_repo.get_patient_id_by_caretaker(current_user.user_id)
            if not patient_id:
                raise CustomException(
                    http_code=404,
                    code='404',
                    message='No patient assigned to this caretaker'
                )
        else:
            raise CustomException(
                http_code=403,
                code='403',
                message='Invalid user role for this operation'
            )
        
        summary = care_plan_service.get_care_plan_summary(patient_id)
        
        logger.info(f"get_care_plan_summary success for patient {patient_id}")
        return DataResponse().success_response(data=summary)
        
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"get_care_plan_summary error: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f'Failed to get care plan summary: {str(e)}'
        )


@router.post('/tasks/{task_id}/refine', response_model=DataResponse[TaskRefinementResponse])
def refine_task(
    task_id: str,
    request: TaskRefinementRequest,
    care_plan_service: CarePlanService = Depends(),
    current_user: User = Depends(login_required)
) -> DataResponse[TaskRefinementResponse]:
    """
    Refine a specific task using AI based on patient feedback.
    
    **Authorization**: PATIENT or CARETAKER role (must own the task).
    
    **Use Case**: Patient finds task too difficult or needs adjustment.
    AI will suggest modifications while keeping the same task type.
    
    **Example Feedback**: 
    - "This exercise is too hard for me"
    - "Can we change the medication time to morning?"
    - "I prefer a different meal option"
    
    **Response**: Updated task with refined description and notes.
    """
    try:
        from uuid import UUID
        
        logger.info(f"refine_task request for task {task_id} from user {current_user.user_id}")
        
        # Parse UUID
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise CustomException(
                http_code=400,
                code='400',
                message='Invalid task ID format'
            )
        
        refined_task = care_plan_service.refine_task_with_ai(
            task_id=task_uuid,
            patient_feedback=request.patient_feedback,
            current_user=current_user
        )
        
        logger.info(f"refine_task success for task {task_id}")
        return DataResponse().success_response(data=refined_task)
        
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"refine_task error: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f'Failed to refine task: {str(e)}'
        )


@router.delete('/{patient_id}', response_model=DataResponse[Dict[str, str]])
def delete_care_plan(
    patient_id: str,
    care_plan_service: CarePlanService = Depends(),
    current_user: User = Depends(login_required)
) -> DataResponse[Dict[str, str]]:
    """
    Delete care plan and all associated tasks.
    
    **Authorization**: CARETAKER role required (must be assigned to this patient).
    
    **Warning**: This action is irreversible. All tasks will be deleted.
    
    **Response**: Success confirmation.
    """
    try:
        from uuid import UUID
        from app.helpers.enums import UserRole
        from app.repository.repo_user import UserRepository
        
        logger.info(f"delete_care_plan request for patient {patient_id}")
        
        # Validate role
        if current_user.role != UserRole.CARETAKER.value:
            raise CustomException(
                http_code=403,
                code='403',
                message='Only caretakers can delete care plans'
            )
        
        # Parse UUID
        try:
            patient_uuid = UUID(patient_id)
        except ValueError:
            raise CustomException(
                http_code=400,
                code='400',
                message='Invalid patient ID format'
            )
        
        # Verify caretaker is assigned to this patient
        user_repo = UserRepository()
        assigned_patient_id = user_repo.get_patient_id_by_caretaker(current_user.user_id)
        if assigned_patient_id != patient_uuid:
            raise CustomException(
                http_code=403,
                code='403',
                message='You are not authorized to delete this care plan'
            )
        
        # Get care plan
        from app.repository.repo_care_plan import CarePlanRepository
        care_plan_repo = CarePlanRepository()
        care_plan = care_plan_repo.get_by_patient_id(patient_uuid)
        
        if not care_plan:
            raise CustomException(
                http_code=404,
                code='404',
                message='Care plan not found'
            )
        
        # Delete cascade
        care_plan_service._delete_care_plan_cascade(care_plan.care_plan_id)
        
        logger.info(f"delete_care_plan success for patient {patient_id}")
        return DataResponse().success_response(
            data={'message': 'Care plan deleted successfully', 'patient_id': patient_id}
        )
        
    except CustomException:
        raise
    except Exception as e:
        logger.error(f"delete_care_plan error: {str(e)}", exc_info=True)
        raise CustomException(
            http_code=500,
            code='500',
            message=f'Failed to delete care plan: {str(e)}'
        )
