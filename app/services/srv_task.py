from datetime import date
from typing import List
from fastapi import Depends
from app.repository.repo_task import TaskRepository
from app.models.model_user import User
from app.helpers.enums import UserRole
from app.schemas.sche_task import TaskDetailResponse, MedicationDetail, NutritionDetail, ExerciseDetail

class TaskService:
    def __init__(self, task_repo: TaskRepository = Depends()):
        self.task_repo = task_repo

    def get_task_detail(self, task_id: str, current_user: User) -> TaskDetailResponse:
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            raise Exception("Task not found")

        # Check ownership (optional, but good practice)
        # Assuming we want to ensure the task belongs to the patient's care plan
        care_plan = self.task_repo.get_care_plan_by_patient_id(current_user.user_id)
        if not care_plan or task.care_plan_id != care_plan.care_plan_id:
             # Also allow if it's a linked task? For now, strict check.
             # If the user is a caretaker, logic might differ.
             # Assuming this API is for PATIENT as per previous context.
             if current_user.role == UserRole.PATIENT.value:
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

    def get_patient_tasks_by_date(self, task_date: date, current_user: User) -> List:

        care_plan = self.task_repo.get_care_plan_by_patient_id(current_user.user_id)
        if not care_plan:
            raise Exception("Care plan not found for this patient.")

        tasks = self.task_repo.get_tasks_by_date(
            care_plan_id=care_plan.care_plan_id,
            task_date=task_date,
            owner_type=UserRole.PATIENT.value
        )
        return tasks

    def get_patient_medication_tasks_by_date(self, task_date: date, current_user: User) -> List[TaskDetailResponse]:
        care_plan = self.task_repo.get_care_plan_by_patient_id(current_user.user_id)
        if not care_plan:
            raise Exception("Care plan not found for this patient.")

        tasks = self.task_repo.get_medication_tasks_by_date(
            care_plan_id=care_plan.care_plan_id,
            task_date=task_date,
            owner_type=UserRole.PATIENT.value
        )
        
        response_list = []
        for task in tasks:
            task_resp = TaskDetailResponse.from_orm(task)
            if task.medication:
                task_resp.medication_detail = MedicationDetail.from_orm(task.medication)
            response_list.append(task_resp)
            
        return response_list

    def complete_task(self, task_id: str, current_user: User):
        if current_user.role != UserRole.PATIENT.value:
            raise Exception("Access denied. Only patients can complete tasks.")

        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            raise Exception("Task not found")

        care_plan = self.task_repo.get_care_plan_by_patient_id(current_user.user_id)
        if not care_plan or task.care_plan_id != care_plan.care_plan_id:
             raise Exception("Access denied. Task does not belong to your care plan.")
        
        task.status = 'COMPLETED'
        return self.task_repo.update_task(task)
