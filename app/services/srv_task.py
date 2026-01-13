from datetime import date
from typing import List, Optional
from fastapi import Depends
from app.repository.repo_task import TaskRepository
from app.repository.repo_user import UserRepository
from app.models.model_user import User
from app.models.model_care_plan import CarePlan
from app.helpers.enums import UserRole
from app.schemas.sche_task import TaskDetailResponse, MedicationDetail, NutritionDetail, ExerciseDetail, TaskResponse, CaretakerTaskResponse

class TaskService:
    def __init__(self, task_repo: TaskRepository = Depends(), user_repo: UserRepository = Depends()):
        self.task_repo = task_repo
        self.user_repo = user_repo

    def get_task_detail(self, task_id: str, current_user: User) -> TaskDetailResponse:
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            raise Exception("Task not found")

        # Check ownership
        care_plan = self._get_care_plan_for_user(current_user)
        if not care_plan or task.care_plan_id != care_plan.care_plan_id:
            raise Exception("Access denied. Task does not belong to your care plan.")
        
        response = TaskDetailResponse.from_orm(task)

        if task.task_type == 'MEDICATION' and task.medication_id:
            medication = self.task_repo.get_medication_detail(task.medication_id)
            if medication:
                response.medication_detail = MedicationDetail.from_orm(medication)
        
        elif task.task_type == 'NUTRITION' and task.nutrition_id:
            nutrition = self.task_repo.get_nutrition_detail(task.nutrition_id)
            if nutrition:
                response.nutrition_detail = NutritionDetail.from_orm(nutrition)

        elif task.task_type == 'EXERCISE' and task.exercise_id:
            exercise = self.task_repo.get_exercise_detail(task.exercise_id)
            if exercise:
                response.exercise_detail = ExerciseDetail.from_orm(exercise)

        return response

    def _get_care_plan_for_user(self, current_user: User) -> Optional[CarePlan]:
        if current_user.role == UserRole.PATIENT.value:
            return self.task_repo.get_care_plan_by_patient_id(current_user.user_id)
        elif current_user.role == UserRole.CARETAKER.value:
            return self.task_repo.get_care_plan_by_caretaker_id(current_user.user_id)
        else:
            raise Exception("Invalid user role")

    def get_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskResponse]:
        care_plan = self._get_care_plan_for_user(current_user)
        if not care_plan:
            raise Exception("Care plan not found for this user.")

        owner_type = current_user.role
        tasks = self.task_repo.get_tasks_by_date(
            care_plan_id=care_plan.care_plan_id,
            task_date=task_date,
            owner_type=owner_type
        )
        return [TaskResponse.from_orm(task) for task in tasks]

    def get_patient_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskResponse]:
        return self.get_tasks_by_date(task_date, current_user)

    def get_medication_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        care_plan = self._get_care_plan_for_user(current_user)
        if not care_plan:
            raise Exception("Care plan not found for this user.")

        owner_type = current_user.role
        tasks = self.task_repo.get_medication_tasks_by_date(
            care_plan_id=care_plan.care_plan_id,
            task_date=task_date,
            owner_type=owner_type
        )
        
        response_list = []
        for task in tasks:
            task_resp = TaskDetailResponse.from_orm(task)
            if task.medication:
                task_resp.medication_detail = MedicationDetail.from_orm(task.medication)
            response_list.append(task_resp)
            
        return response_list

    def get_patient_medication_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        return self.get_medication_tasks_by_date(task_date, current_user)

    def get_nutrition_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        care_plan = self._get_care_plan_for_user(current_user)
        if not care_plan:
            raise Exception("Care plan not found for this user.")

        owner_type = current_user.role
        tasks = self.task_repo.get_nutrition_tasks_by_date(
            care_plan_id=care_plan.care_plan_id,
            task_date=task_date,
            owner_type=owner_type
        )
        
        response_list = []
        for task in tasks:
            task_resp = TaskDetailResponse.from_orm(task)
            if task.nutrition_id:
                task_resp.nutrition_detail = NutritionDetail.from_orm(task.nutrition)
            response_list.append(task_resp)
            
        return response_list

    def get_patient_nutrition_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        return self.get_nutrition_tasks_by_date(task_date, current_user)

    def get_exercise_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        care_plan = self._get_care_plan_for_user(current_user)
        if not care_plan:
            raise Exception("Care plan not found for this user.")

        owner_type = current_user.role
        tasks = self.task_repo.get_exercise_tasks_by_date(
            care_plan_id=care_plan.care_plan_id,
            task_date=task_date,
            owner_type=owner_type
        )
        
        response_list = []
        for task in tasks:
            task_resp = TaskDetailResponse.from_orm(task)
            if task.exercise_id:
                task_resp.exercise_detail = ExerciseDetail.from_orm(task.exercise)
            response_list.append(task_resp)
            
        return response_list

    def get_patient_exercise_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        return self.get_exercise_tasks_by_date(task_date, current_user)
        if current_user.role != UserRole.CARETAKER.value:
            raise Exception("Access denied. Only caretakers can access this.")

        patient_id = self.user_repo.get_patient_id_by_caretaker(current_user.user_id)
        if not patient_id:
            raise Exception("No patient assigned to this caretaker.")

        care_plan = self.task_repo.get_care_plan_by_patient_id(patient_id)
        if not care_plan:
            # It's possible the patient has no care plan yet. Return empty list.
            return []

        tasks = self.task_repo.get_tasks_by_care_plan(care_plan.care_plan_id)
        return [TaskResponse.from_orm(task) for task in tasks]

    def get_caretaker_tasks_with_linked_info(self, current_user: User) -> List[CaretakerTaskResponse]:
        if current_user.role != UserRole.CARETAKER.value:
            raise Exception("Access denied. Only caretakers can access this.")

        patient_id = self.user_repo.get_patient_id_by_caretaker(current_user.user_id)
        if not patient_id:
            raise Exception("No patient assigned to this caretaker.")

        care_plan = self.task_repo.get_care_plan_by_patient_id(patient_id)
        if not care_plan:
            return []

        tasks = self.task_repo.get_caretaker_tasks(care_plan.care_plan_id)
        
        return [CaretakerTaskResponse.from_orm(task) for task in tasks]

    def complete_task(self, task_id: str, current_user: User):
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            raise Exception("Task not found")

        # Check access based on user role
        if current_user.role == UserRole.PATIENT.value:
            # Patient can only complete their own tasks
            care_plan = self.task_repo.get_care_plan_by_patient_id(current_user.user_id)
            if not care_plan or task.care_plan_id != care_plan.care_plan_id:
                raise Exception("Access denied. Task does not belong to your care plan.")
        elif current_user.role == UserRole.CARETAKER.value:
            # Caretaker can complete tasks for their assigned patient
            care_plan = self.task_repo.get_care_plan_by_caretaker_id(current_user.user_id)
            if not care_plan or task.care_plan_id != care_plan.care_plan_id:
                raise Exception("Access denied. Task does not belong to your patient's care plan.")
        else:
            raise Exception("Access denied. Invalid user role.")
        
        task.status = 'DONE'
        return self.task_repo.update_task(task)
