from typing import Any, List
from datetime import date
import logging
from fastapi import APIRouter, Depends, Query

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_task import TaskResponse, TaskDetailResponse, CaretakerTaskResponse
from app.services.srv_task import TaskService
from app.services.srv_user import UserService
from app.models.model_user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get('/caretaker/tasks', dependencies=[Depends(login_required)], response_model=DataResponse[List[TaskResponse]])
def get_caretaker_tasks(
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve all tasks assigned to patients under caretaker's supervision.
    
    This API allows caretakers to view all care plan tasks for their assigned patients, 
    including medication reminders, exercise routines, and nutritional tasks.
    
    **Authorization**: CARETAKER role required.
    
    **Process**:
    1. Validates user has caretaker role
    2. Retrieves all tasks for assigned patients from database
    
    **Response**: List of task summaries for caretaker's patients.
    """
    try:
        logger.info(f"get_caretaker_tasks request: caretaker_id={current_user.user_id}")
        tasks = task_service.get_caretaker_tasks(current_user)
        logger.info(f"get_caretaker_tasks success: {len(tasks)} tasks retrieved")
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        logger.error(f"get_caretaker_tasks error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/caretaker/tasks-with-patient-info', dependencies=[Depends(login_required)], response_model=DataResponse[List[CaretakerTaskResponse]])
def get_caretaker_tasks_with_patient_info(
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve all tasks with linked patient information for caretaker.
    
    This API provides caretakers with comprehensive task information including patient details, 
    task status, and completion tracking for better care management.
    
    **Authorization**: CARETAKER role required.
    
    **Process**:
    1. Validates user has caretaker role
    2. Retrieves tasks with associated patient information from database
    
    **Response**: List of tasks with patient linkage details.
    """
    try:
        logger.info(f"get_caretaker_tasks_with_patient_info request: caretaker_id={current_user.user_id}")
        tasks = task_service.get_caretaker_tasks_with_linked_info(current_user)
        logger.info(f"get_caretaker_tasks_with_patient_info success: {len(tasks)} tasks retrieved")
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        logger.error(f"get_caretaker_tasks_with_patient_info error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/{task_id}', dependencies=[Depends(login_required)], response_model=DataResponse[TaskDetailResponse])
def get_task_detail(
    task_id: str,
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve detailed information for a specific task.
    
    This API provides comprehensive details about a task including instructions, 
    completion status, associated patient information, and any additional notes.
    
    **Authorization**: Authenticated user required (task owner or assigned caretaker).
    
    **Process**:
    1. Validates user access to the specified task
    2. Retrieves detailed task information from database
    
    **Response**: Complete task details with all associated information.
    """
    try:
        logger.info(f"get_task_detail request: task_id={task_id}, user_id={current_user.user_id}")
        task_detail = task_service.get_task_detail(task_id, current_user)
        logger.info(f"get_task_detail success: task_id={task_id}")
        return DataResponse().success_response(data=task_detail)
    except Exception as e:
        logger.error(f"get_task_detail error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/patient/by-date', dependencies=[Depends(login_required)], response_model=DataResponse[List[TaskResponse]])
def get_patient_tasks_by_date(
    task_date: date = Query(..., description="Date to filter tasks (YYYY-MM-DD)"),
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve patient's daily tasks for a specific date.
    
    This API allows patients to view all their care plan tasks scheduled for a particular day, 
    including medication, exercise, and nutrition tasks.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient tasks
    2. Filters tasks by specified date from database
    
    **Response**: List of patient's tasks for the requested date.
    """
    try:
        logger.info(f"get_patient_tasks_by_date request: date={task_date}, user_id={current_user.user_id}")
        tasks = task_service.get_patient_tasks_by_date(task_date, current_user)
        logger.info(f"get_patient_tasks_by_date success: {len(tasks)} tasks for date {task_date}")
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        logger.error(f"get_patient_tasks_by_date error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/patient/medication-tasks', dependencies=[Depends(login_required)], response_model=DataResponse[List[TaskDetailResponse]])
def get_patient_medication_tasks_by_date(
    task_date: date = Query(..., description="Date to filter tasks (YYYY-MM-DD)"),
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve patient's medication tasks for a specific date.
    
    This API provides detailed medication tasks for patients on a given date, 
    including dosage, timing, and administration instructions.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient medication tasks
    2. Filters medication tasks by specified date from database
    
    **Response**: List of detailed medication tasks for the requested date.
    """
    try:
        logger.info(f"get_patient_medication_tasks_by_date request: date={task_date}, user_id={current_user.user_id}")
        tasks = task_service.get_patient_medication_tasks_by_date(task_date, current_user)
        logger.info(f"get_patient_medication_tasks_by_date success: {len(tasks)} medication tasks for date {task_date}")
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        logger.error(f"get_patient_medication_tasks_by_date error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/patient/nutrition-tasks', dependencies=[Depends(login_required)], response_model=DataResponse[List[TaskDetailResponse]])
def get_patient_nutrition_tasks_by_date(
    task_date: date = Query(..., description="Date to filter tasks (YYYY-MM-DD)"),
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve patient's nutrition tasks for a specific date.
    
    This API provides detailed nutrition tasks for patients on a given date, 
    including meal plans, dietary recommendations, and nutritional guidelines.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient nutrition tasks
    2. Filters nutrition tasks by specified date from database
    
    **Response**: List of detailed nutrition tasks for the requested date.
    """
    try:
        logger.info(f"get_patient_nutrition_tasks_by_date request: date={task_date}, user_id={current_user.user_id}")
        tasks = task_service.get_patient_nutrition_tasks_by_date(task_date, current_user)
        logger.info(f"get_patient_nutrition_tasks_by_date success: {len(tasks)} nutrition tasks for date {task_date}")
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        logger.error(f"get_patient_nutrition_tasks_by_date error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/patient/exercise-tasks', dependencies=[Depends(login_required)], response_model=DataResponse[List[TaskDetailResponse]])
def get_patient_exercise_tasks_by_date(
    task_date: date = Query(..., description="Date to filter tasks (YYYY-MM-DD)"),
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Retrieve patient's exercise tasks for a specific date.
    
    This API provides detailed exercise tasks for patients on a given date, 
    including workout routines, physical therapy exercises, and activity recommendations.
    
    **Authorization**: Authenticated user required (patient or assigned caretaker).
    
    **Process**:
    1. Validates user access to patient exercise tasks
    2. Filters exercise tasks by specified date from database
    
    **Response**: List of detailed exercise tasks for the requested date.
    """
    try:
        logger.info(f"get_patient_exercise_tasks_by_date request: date={task_date}, user_id={current_user.user_id}")
        tasks = task_service.get_patient_exercise_tasks_by_date(task_date, current_user)
        logger.info(f"get_patient_exercise_tasks_by_date success: {len(tasks)} exercise tasks for date {task_date}")
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        logger.error(f"get_patient_exercise_tasks_by_date error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))

@router.put('/patient/{task_id}/complete', dependencies=[Depends(login_required)], response_model=DataResponse[TaskResponse])
def complete_task(
    task_id: str,
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    """
    Mark a patient task as completed.
    
    This API allows patients to mark their care plan tasks as completed, 
    updating the task status and completion timestamp.
    
    **Authorization**: Authenticated user required (task owner or assigned caretaker).
    
    **Process**:
    1. Validates user access to the specified task
    2. Updates task status to completed in database
    3. Returns updated task information
    
    **Response**: Updated task details with completion status.
    """
    try:
        logger.info(f"complete_task request: task_id={task_id}, user_id={current_user.user_id}")
        task = task_service.complete_task(task_id, current_user)
        logger.info(f"complete_task success: task_id={task_id}")
        return DataResponse().success_response(data=task)
    except Exception as e:
        logger.error(f"complete_task error: {str(e)}", exc_info=True)
        raise CustomException(http_code=400, code='400', message=str(e))
