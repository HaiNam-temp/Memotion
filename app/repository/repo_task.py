from typing import List, Optional
from datetime import date
from fastapi import Depends
from sqlalchemy import cast, Date
from sqlalchemy.orm import joinedload
from app.db.base import get_db
from app.models.model_task import Task
from app.models.model_care_plan import CarePlan
from app.models.model_medication_library import MedicationLibrary
from app.models.model_nutrition_library import NutritionLibrary
from app.models.model_exercise_library import ExerciseLibrary

class TaskRepository:
    def __init__(self, db_session = Depends(get_db)):
        self.db = db_session

    def create_task(self, task_data: Task) -> Task:
        self.db.add(task_data)
        self.db.commit()
        self.db.refresh(task_data)
        return task_data

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    def get_medication_detail(self, medication_id: str) -> Optional[MedicationLibrary]:
        return self.db.query(MedicationLibrary).filter(MedicationLibrary.medication_id == medication_id).first()

    def get_nutrition_detail(self, nutrition_id: str) -> Optional[NutritionLibrary]:
        return self.db.query(NutritionLibrary).filter(NutritionLibrary.nutrition_id == nutrition_id).first()

    def get_exercise_detail(self, exercise_id: str) -> Optional[ExerciseLibrary]:
        return self.db.query(ExerciseLibrary).filter(ExerciseLibrary.exercise_id == exercise_id).first()

    def get_care_plan_by_patient_id(self, patient_id: str) -> Optional[CarePlan]:
        return self.db.query(CarePlan).filter(CarePlan.patient_id == patient_id).first()

    def update_task(self, task: Task) -> Task:
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_tasks_by_date(self, care_plan_id: str, task_date: date, owner_type: str) -> List[Task]:
        return self.db.query(Task).filter(
            Task.care_plan_id == care_plan_id,
            cast(Task.task_duedate, Date) == task_date,
            Task.owner_type == owner_type
        ).all()

    def get_medication_tasks_by_date(self, care_plan_id: str, task_date: date, owner_type: str) -> List[Task]:
        return self.db.query(Task).join(MedicationLibrary, Task.medication_id == MedicationLibrary.medication_id).filter(
            Task.care_plan_id == care_plan_id,
            cast(Task.task_duedate, Date) == task_date,
            Task.owner_type == owner_type,
            Task.task_type == 'MEDICATION'
        ).all()

    def get_tasks_by_care_plan(self, care_plan_id: str) -> List[Task]:
        return self.db.query(Task).filter(Task.care_plan_id == care_plan_id).all()

    def get_caretaker_tasks(self, care_plan_id: str) -> List[Task]:
        return self.db.query(Task).options(joinedload(Task.linked_task)).filter(
            Task.care_plan_id == care_plan_id,
            Task.owner_type == 'CARETAKER'
        ).all()

    def delete_tasks_by_care_plan_id(self, care_plan_id: str) -> None:
        self.db.query(Task).filter(Task.care_plan_id == care_plan_id).delete()
        self.db.commit()
