from typing import Any, List
from datetime import date
from fastapi import APIRouter, Depends, Query

from app.helpers.exception_handler import CustomException
from app.helpers.login_manager import login_required
from app.schemas.sche_base import DataResponse
from app.schemas.sche_task import TaskResponse, TaskDetailResponse
from app.services.srv_task import TaskService
from app.services.srv_user import UserService
from app.models.model_user import User

router = APIRouter()

@router.get('/{task_id}', dependencies=[Depends(login_required)], response_model=DataResponse[TaskDetailResponse])
def get_task_detail(
    task_id: str,
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        task_detail = task_service.get_task_detail(task_id, current_user)
        return DataResponse().success_response(data=task_detail)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))

@router.get('/patient/by-date', dependencies=[Depends(login_required)], response_model=DataResponse[List[TaskResponse]])
def get_patient_tasks_by_date(
    task_date: date = Query(..., description="Date to filter tasks (YYYY-MM-DD)"),
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        tasks = task_service.get_patient_tasks_by_date(task_date, current_user)
        return DataResponse().success_response(data=tasks)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))

@router.put('/patient/{task_id}/complete', dependencies=[Depends(login_required)], response_model=DataResponse[TaskResponse])
def complete_task(
    task_id: str,
    task_service: TaskService = Depends(),
    current_user: User = Depends(UserService.get_current_user)
) -> Any:
    try:
        task = task_service.complete_task(task_id, current_user)
        return DataResponse().success_response(data=task)
    except Exception as e:
        raise CustomException(http_code=400, code='400', message=str(e))
