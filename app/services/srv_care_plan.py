"""
Care Plan Service - Orchestrates AI-powered care plan generation.
Coordinates between AI agent, repositories, and domain logic.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import Depends
from uuid import UUID

from app.ai_agent.careplan_agent import CarePlanAgent
from app.ai_agent.mappers import (
    CarePlanMapper,
    PatientProfileMapper,
    LibraryMapper
)
from app.repository.repo_care_plan import CarePlanRepository
from app.repository.repo_patient_profile import PatientProfileRepository
from app.repository.repo_task import TaskRepository
from app.repository.repo_medication_library import MedicationLibraryRepository
from app.repository.repo_nutrition_library import NutritionLibraryRepository
from app.repository.repo_exercise_library import ExerciseLibraryRepository
from app.repository.repo_user import UserRepository
from app.models.model_care_plan import CarePlan
from app.models.model_task import Task
from app.models.model_user import User
from app.helpers.enums import UserRole
from app.helpers.exception_handler import CustomException

logger = logging.getLogger(__name__)


class CarePlanService:
    """
    Service for AI-powered care plan generation and management.
    Orchestrates the entire workflow from data gathering to task creation.
    """

    def __init__(
        self,
        care_plan_repo: CarePlanRepository = Depends(),
        profile_repo: PatientProfileRepository = Depends(),
        task_repo: TaskRepository = Depends(),
        medication_repo: MedicationLibraryRepository = Depends(),
        nutrition_repo: NutritionLibraryRepository = Depends(),
        exercise_repo: ExerciseLibraryRepository = Depends(),
        user_repo: UserRepository = Depends()
    ):
        """
        Initialize service with repository dependencies.

        Args:
            care_plan_repo: Care plan repository.
            profile_repo: Patient profile repository.
            task_repo: Task repository.
            medication_repo: Medication library repository.
            nutrition_repo: Nutrition library repository.
            exercise_repo: Exercise library repository.
            user_repo: User repository.
        """
        self.care_plan_repo = care_plan_repo
        self.profile_repo = profile_repo
        self.task_repo = task_repo
        self.medication_repo = medication_repo
        self.nutrition_repo = nutrition_repo
        self.exercise_repo = exercise_repo
        self.user_repo = user_repo
        self.ai_agent = CarePlanAgent()

    def generate_care_plan_for_patient(
        self,
        patient_id: UUID,
        caretaker_id: UUID,
        plan_duration_days: int = 7,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate AI-powered care plan following layered architecture rules."""
        try:
            logger.info(
                f"Generating care plan for patient {patient_id} (duration={plan_duration_days}d, regenerate={regenerate})"
            )

            existing_plan = self._get_existing_plan(patient_id)
            self._guard_plan_regeneration(existing_plan, regenerate)

            patient_profile, therapy_detail = self._load_patient_profile(patient_id)
            libraries = self._load_libraries()

            ai_payload = self._build_ai_payload(patient_profile, therapy_detail, libraries)
            ai_generated_plan = self._generate_plan_from_ai(ai_payload, plan_duration_days)
            ai_generated_plan = self._validate_ai_plan_against_libraries(ai_generated_plan, libraries)

            created_plan = self._persist_care_plan(existing_plan, regenerate, patient_id, caretaker_id)
            created_tasks = self._persist_tasks(ai_generated_plan, created_plan.care_plan_id)

            return self._build_generation_response(
                created_plan=created_plan,
                patient_id=patient_id,
                caretaker_id=caretaker_id,
                plan_duration_days=plan_duration_days,
                created_tasks=created_tasks,
                ai_generated_plan=ai_generated_plan
            )

        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate care plan: {str(e)}", exc_info=True)
            raise CustomException(
                http_code=500,
                code='500',
                message=f'Care plan generation failed: {str(e)}'
            )

    def update_care_plan_for_patient(
        self,
        patient_id: UUID,
        caretaker_id: UUID,
        plan_duration_days: int = 7
    ) -> Dict[str, Any]:
        """Update existing care plan with new tasks based on current patient profile."""
        try:
            logger.info(
                f"Updating care plan for patient {patient_id} (duration={plan_duration_days}d)"
            )

            existing_plan = self._get_existing_plan(patient_id)
            if not existing_plan:
                raise CustomException(
                    http_code=404,
                    code='404',
                    message='No existing care plan found for this patient. Please generate a care plan first.'
                )

            patient_profile, therapy_detail = self._load_patient_profile(patient_id)
            libraries = self._load_libraries()

            ai_payload = self._build_ai_payload(patient_profile, therapy_detail, libraries)
            ai_generated_plan = self._generate_plan_from_ai(ai_payload, plan_duration_days)
            ai_generated_plan = self._validate_ai_plan_against_libraries(ai_generated_plan, libraries)

            # Delete existing tasks
            self.task_repo.delete_tasks_by_care_plan_id(existing_plan.care_plan_id)

            # Create new tasks
            created_tasks = self._persist_tasks(ai_generated_plan, existing_plan.care_plan_id)

            # Update care plan updated_at timestamp
            existing_plan.updated_at = datetime.now()
            self.care_plan_repo.update(existing_plan)

            return self._build_update_response(
                updated_plan=existing_plan,
                patient_id=patient_id,
                caretaker_id=caretaker_id,
                plan_duration_days=plan_duration_days,
                updated_tasks=created_tasks,
                ai_generated_plan=ai_generated_plan
            )

        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to update care plan: {str(e)}", exc_info=True)
            raise CustomException(
                http_code=500,
                code='500',
                message=f'Care plan update failed: {str(e)}'
            )

    # ---------- Private helpers (keep service lean & testable) ----------
    def _get_existing_plan(self, patient_id: UUID) -> CarePlan:
        return self.care_plan_repo.get_by_patient_id(patient_id)

    def _guard_plan_regeneration(self, existing_plan: CarePlan, regenerate: bool) -> None:
        if existing_plan and not regenerate:
            raise CustomException(
                http_code=400,
                code='400',
                message='Care plan already exists for this patient. Use regenerate=true to recreate.'
            )

    def _load_patient_profile(self, patient_id: UUID):
        patient_profile = self.profile_repo.get_profile_by_patient_id(patient_id)
        if not patient_profile:
            raise CustomException(
                http_code=404,
                code='404',
                message='Patient profile not found. Please create patient profile first.'
            )

        therapy_detail = None
        if patient_profile.disease_type == 'PHYSICAL_THERAPY':
            therapy_detail = self.profile_repo.get_physical_therapy_by_patient_id(patient_id)

        return patient_profile, therapy_detail

    def _load_libraries(self) -> Dict[str, List[Any]]:
        return {
            'medications': self.medication_repo.get_all(limit=50),
            'nutrition': self.nutrition_repo.get_all(limit=50),
            'exercises': self.exercise_repo.get_all(limit=50),
        }

    def _build_ai_payload(self, patient_profile: Any, therapy_detail: Any, libraries: Dict[str, List[Any]]) -> Dict[str, Any]:
        profile_dict = PatientProfileMapper.map_profile_to_ai_input(patient_profile, therapy_detail)
        return {
            'profile': profile_dict,
            'medications': LibraryMapper.map_medications_to_ai_format(libraries['medications']),
            'nutrition': LibraryMapper.map_nutrition_to_ai_format(libraries['nutrition']),
            'exercises': LibraryMapper.map_exercises_to_ai_format(libraries['exercises']),
        }

    def _generate_plan_from_ai(self, ai_payload: Dict[str, Any], plan_duration_days: int) -> Dict[str, Any]:
        logger.info("Calling AI agent to generate care plan...")
        return self.ai_agent.generate_care_plan(
            patient_profile=ai_payload['profile'],
            patient_therapy_detail=ai_payload['profile'].get('therapy_detail'),
            medication_library=ai_payload['medications'],
            nutrition_library=ai_payload['nutrition'],
            exercise_library=ai_payload['exercises'],
            plan_duration_days=plan_duration_days,
            current_date=datetime.now()
        )

    def _validate_ai_plan_against_libraries(
        self,
        ai_plan: Dict[str, Any],
        libraries: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Ensure AI tasks strictly reference existing library items by ID."""
        if not ai_plan or 'tasks' not in ai_plan:
            raise CustomException(
                http_code=422,
                code='422',
                message='AI plan is empty or missing tasks.'
            )

        med_map = {str(med.medication_id): med for med in libraries.get('medications', [])}
        nutrition_map = {str(nut.nutrition_id): nut for nut in libraries.get('nutrition', [])}
        exercise_map = {str(ex.exercise_id): ex for ex in libraries.get('exercises', [])}

        sanitized_tasks: List[Dict[str, Any]] = []
        dropped_tasks: List[str] = []

        for idx, ai_task in enumerate(ai_plan.get('tasks', [])):
            task_type = ai_task.get('task_type')
            resource_id = ai_task.get('resource_id')
            normalized = dict(ai_task)

            if task_type == 'MEDICATION':
                med_id = normalized.get('medication_id') or resource_id
                if med_id and str(med_id) in med_map:
                    med = med_map[str(med_id)]
                    normalized['medication_id'] = str(med_id)
                    normalized.setdefault('title', f"Take {med.name}")
                    normalized.setdefault('description', med.description or f"Use {med.name} as prescribed")
                    normalized.setdefault('owner_type', 'PATIENT')
                    sanitized_tasks.append(normalized)
                else:
                    dropped_tasks.append(f"task[{idx}] missing valid medication_id")

            elif task_type == 'NUTRITION':
                nut_id = normalized.get('nutrition_id') or resource_id
                if nut_id and str(nut_id) in nutrition_map:
                    nut = nutrition_map[str(nut_id)]
                    normalized['nutrition_id'] = str(nut_id)
                    normalized.setdefault('title', f"Nutrition: {nut.name}")
                    normalized.setdefault('description', nut.description or f"Meal: {nut.name}")
                    normalized.setdefault('owner_type', 'PATIENT')
                    sanitized_tasks.append(normalized)
                else:
                    dropped_tasks.append(f"task[{idx}] missing valid nutrition_id")

            elif task_type == 'EXERCISE':
                ex_id = normalized.get('exercise_id') or resource_id
                if ex_id and str(ex_id) in exercise_map:
                    ex = exercise_map[str(ex_id)]
                    normalized['exercise_id'] = str(ex_id)
                    normalized.setdefault('title', f"Exercise: {ex.name}")
                    normalized.setdefault('description', ex.description or f"Perform {ex.name}")
                    normalized.setdefault('owner_type', 'PATIENT')
                    sanitized_tasks.append(normalized)
                else:
                    dropped_tasks.append(f"task[{idx}] missing valid exercise_id")

            else:
                dropped_tasks.append(f"task[{idx}] has unsupported task_type {task_type}")

        if dropped_tasks:
            logger.warning("Dropped AI tasks due to invalid references: %s", "; ".join(dropped_tasks))

        if not sanitized_tasks:
            raise CustomException(
                http_code=422,
                code='422',
                message='No valid tasks generated from available libraries.'
            )

        ai_plan['tasks'] = sanitized_tasks
        return ai_plan

    def _persist_care_plan(
        self,
        existing_plan: CarePlan,
        regenerate: bool,
        patient_id: UUID,
        caretaker_id: UUID
    ) -> CarePlan:
        if existing_plan and regenerate:
            self._delete_care_plan_cascade(existing_plan.care_plan_id)

        new_care_plan = CarePlan(patient_id=patient_id, caretaker_id=caretaker_id)
        return self.care_plan_repo.create(new_care_plan)

    def _persist_tasks(self, ai_generated_plan: Dict[str, Any], care_plan_id: UUID) -> List[Task]:
        task_models = CarePlanMapper.map_ai_plan_to_task_models(
            ai_plan=ai_generated_plan,
            care_plan_id=care_plan_id,
            start_date=datetime.now()
        )

        created_tasks: List[Task] = []
        for task_dict in task_models:
            task = Task(**task_dict)
            created_tasks.append(self.task_repo.create_task(task))

        logger.info(f"Successfully created care plan with {len(created_tasks)} tasks")
        return created_tasks

    def _build_update_response(
        self,
        updated_plan: CarePlan,
        patient_id: UUID,
        caretaker_id: UUID,
        plan_duration_days: int,
        updated_tasks: List[Task],
        ai_generated_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            'care_plan_id': str(updated_plan.care_plan_id),
            'patient_id': str(patient_id),
            'caretaker_id': str(caretaker_id),
            'plan_duration_days': plan_duration_days,
            'total_tasks': len(updated_tasks),
            'tasks_updated': len(updated_tasks),
            'recommendations': ai_generated_plan.get('recommendations', []),
            'updated_at': updated_plan.updated_at.isoformat()
        }

    def generate_care_plan_by_caretaker(
        self,
        current_user: User,
        plan_duration_days: int = 7,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate care plan for the patient assigned to the caretaker.
        Also updates caretaker's is_first_login to False if it was True.
        """
        # Get assigned patient
        patient = self.user_repo.get_assigned_patient(current_user.user_id)
        if not patient:
            raise CustomException(
                http_code=404,
                code='404',
                message='No patient assigned to this caretaker.'
            )

        # Update caretaker's is_first_login to False after first care plan generation
        if current_user.is_first_login:
            current_user.is_first_login = False
            self.user_repo.update(current_user)
            logger.info(f"Updated is_first_login=False for caretaker {current_user.user_id}")
        
        # Also update patient's is_first_login
        if patient.is_first_login:
            patient.is_first_login = False
            self.user_repo.update(patient)
            logger.info(f"Updated is_first_login=False for patient {patient.user_id}")

        return self.generate_care_plan_for_patient(
            patient_id=patient.user_id,
            caretaker_id=current_user.user_id,
            plan_duration_days=plan_duration_days,
            regenerate=regenerate
        )

    def update_care_plan_by_caretaker(
        self,
        current_user: User,
        plan_duration_days: int = 7
    ) -> Dict[str, Any]:
        """
        Update care plan for the patient assigned to the caretaker.
        Includes regeneration of caretaker support tasks.

        Args:
            current_user: Current logged-in caretaker.
            plan_duration_days: Duration of care plan.

        Returns:
            Updated care plan data including caretaker tasks.

        Raises:
            CustomException: If user is not caretaker or patient not found.
        """
        # Validate role
        if current_user.role != UserRole.CARETAKER.value:
            raise CustomException(
                http_code=403,
                code='403',
                message='Only caretakers can update care plans'
            )

        # Get assigned patient
        patient_id = self.user_repo.get_patient_id_by_caretaker(current_user.user_id)
        if not patient_id:
            raise CustomException(
                http_code=404,
                code='404',
                message='No patient assigned to this caretaker'
            )

        # Update patient care plan
        result = self.update_care_plan_for_patient(
            patient_id=patient_id,
            caretaker_id=current_user.user_id,
            plan_duration_days=plan_duration_days
        )

        # Generate caretaker support tasks
        care_plan_id = result['care_plan_id']
        patient_tasks = self.task_repo.get_tasks_by_care_plan_and_owner(care_plan_id, 'PATIENT')
        
        # Convert Task objects to dicts for AI agent
        patient_task_dicts = []
        for task in patient_tasks:
            task_dict = {
                'task_id': str(task.task_id),
                'title': task.title,
                'description': task.description,
                'task_type': task.task_type,
                'owner_type': task.owner_type,
                'task_duedate': task.task_duedate.isoformat() if task.task_duedate else None,
                'status': task.status,
            }
            if task.medication_id:
                task_dict['medication_id'] = str(task.medication_id)
            if task.nutrition_id:
                task_dict['nutrition_id'] = str(task.nutrition_id)
            if task.exercise_id:
                task_dict['exercise_id'] = str(task.exercise_id)
            patient_task_dicts.append(task_dict)

        # Generate caretaker tasks using AI agent
        caretaker_task_dicts = self.ai_agent.generate_caretaker_tasks(patient_task_dicts)

        # Persist caretaker tasks
        created_caretaker_tasks = []
        for caretaker_task_dict in caretaker_task_dicts:
            caretaker_task_dict['care_plan_id'] = care_plan_id
            # Remove priority if present (Task model doesn't have priority field)
            caretaker_task_dict.pop('priority', None)
            # Convert linked_task_id to UUID
            if 'linked_task_id' in caretaker_task_dict:
                caretaker_task_dict['linked_task_id'] = UUID(caretaker_task_dict['linked_task_id'])
            # Convert task_duedate to datetime
            if 'task_duedate' in caretaker_task_dict and caretaker_task_dict['task_duedate']:
                caretaker_task_dict['task_duedate'] = datetime.fromisoformat(caretaker_task_dict['task_duedate'])
            caretaker_task = Task(**caretaker_task_dict)
            created_caretaker_tasks.append(self.task_repo.create_task(caretaker_task))

        # Update response with caretaker tasks info
        result['caretaker_tasks_updated'] = len(created_caretaker_tasks)
        result['total_tasks'] += len(created_caretaker_tasks)

        logger.info(f"Updated care plan with {result['total_tasks']} total tasks ({result['tasks_updated']} patient + {len(created_caretaker_tasks)} caretaker)")

        return result

    def _build_generation_response(
        self,
        created_plan: CarePlan,
        patient_id: UUID,
        caretaker_id: UUID,
        plan_duration_days: int,
        created_tasks: List[Task],
        ai_generated_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            'care_plan_id': str(created_plan.care_plan_id),
            'patient_id': str(patient_id),
            'caretaker_id': str(caretaker_id),
            'plan_duration_days': plan_duration_days,
            'total_tasks': len(created_tasks),
            'tasks_created': len(created_tasks),
            'recommendations': ai_generated_plan.get('recommendations', []),
            'generated_at': created_plan.created_at.isoformat()
        }

    def generate_care_plan_by_caretaker(
        self,
        current_user: User,
        plan_duration_days: int = 7,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate care plan for the patient assigned to this caretaker.
        Includes generation of caretaker support tasks.

        Args:
            current_user: Current logged-in caretaker.
            plan_duration_days: Duration of care plan.
            regenerate: Whether to regenerate existing plan.

        Returns:
            Generated care plan data including caretaker tasks.

        Raises:
            CustomException: If user is not caretaker or patient not found.
        """
        # Validate role
        if current_user.role != UserRole.CARETAKER.value:
            raise CustomException(
                http_code=403,
                code='403',
                message='Only caretakers can generate care plans'
            )

        # Get assigned patient
        patient_id = self.user_repo.get_patient_id_by_caretaker(current_user.user_id)
        if not patient_id:
            raise CustomException(
                http_code=404,
                code='404',
                message='No patient assigned to this caretaker'
            )

        # Generate patient care plan
        result = self.generate_care_plan_for_patient(
            patient_id=patient_id,
            caretaker_id=current_user.user_id,
            plan_duration_days=plan_duration_days,
            regenerate=regenerate
        )

        # Generate caretaker support tasks
        care_plan_id = result['care_plan_id']
        patient_tasks = self.task_repo.get_tasks_by_care_plan_and_owner(care_plan_id, 'PATIENT')
        
        # Convert Task objects to dicts for AI agent
        patient_task_dicts = []
        for task in patient_tasks:
            task_dict = {
                'task_id': str(task.task_id),
                'title': task.title,
                'description': task.description,
                'task_type': task.task_type,
                'owner_type': task.owner_type,
                'task_duedate': task.task_duedate.isoformat() if task.task_duedate else None,
                'status': task.status,
            }
            if task.medication_id:
                task_dict['medication_id'] = str(task.medication_id)
            if task.nutrition_id:
                task_dict['nutrition_id'] = str(task.nutrition_id)
            if task.exercise_id:
                task_dict['exercise_id'] = str(task.exercise_id)
            patient_task_dicts.append(task_dict)

        # Generate caretaker tasks using AI agent
        caretaker_task_dicts = self.ai_agent.generate_caretaker_tasks(patient_task_dicts)

        # Persist caretaker tasks
        created_caretaker_tasks = []
        for caretaker_task_dict in caretaker_task_dicts:
            caretaker_task_dict['care_plan_id'] = care_plan_id
            # Remove priority if present (Task model doesn't have priority field)
            caretaker_task_dict.pop('priority', None)
            # Convert linked_task_id to UUID
            if 'linked_task_id' in caretaker_task_dict:
                caretaker_task_dict['linked_task_id'] = UUID(caretaker_task_dict['linked_task_id'])
            # Convert task_duedate to datetime
            if 'task_duedate' in caretaker_task_dict and caretaker_task_dict['task_duedate']:
                caretaker_task_dict['task_duedate'] = datetime.fromisoformat(caretaker_task_dict['task_duedate'])
            caretaker_task = Task(**caretaker_task_dict)
            created_caretaker_tasks.append(self.task_repo.create_task(caretaker_task))

        # Update response with caretaker tasks info
        result['caretaker_tasks_created'] = len(created_caretaker_tasks)
        result['total_tasks'] += len(created_caretaker_tasks)

        logger.info(f"Generated care plan with {result['total_tasks']} total tasks ({result['tasks_created']} patient + {len(created_caretaker_tasks)} caretaker)")

        return result

    def get_care_plan_summary(self, patient_id: UUID) -> Dict[str, Any]:
        """
        Get summary of care plan for a patient.

        Args:
            patient_id: Patient's user ID.

        Returns:
            Care plan summary with task statistics.

        Raises:
            CustomException: If care plan not found.
        """
        care_plan = self.care_plan_repo.get_by_patient_id(patient_id)
        if not care_plan:
            raise CustomException(
                http_code=404,
                code='404',
                message='Care plan not found for this patient'
            )

        # Get task statistics
        tasks = self.task_repo.get_tasks_by_care_plan(care_plan.care_plan_id)
        
        task_stats = {
            'total': len(tasks),
            'pending': sum(1 for t in tasks if t.status == 'PENDING'),
            'done': sum(1 for t in tasks if t.status == 'DONE'),
            'by_type': {}
        }

        for task in tasks:
            task_type = task.task_type
            if task_type not in task_stats['by_type']:
                task_stats['by_type'][task_type] = 0
            task_stats['by_type'][task_type] += 1

        return {
            'care_plan_id': str(care_plan.care_plan_id),
            'patient_id': str(care_plan.patient_id),
            'caretaker_id': str(care_plan.caretaker_id),
            'created_at': care_plan.created_at.isoformat(),
            'updated_at': care_plan.updated_at.isoformat(),
            'task_statistics': task_stats
        }

    def _delete_care_plan_cascade(self, care_plan_id: UUID):
        """
        Delete care plan and all associated tasks.

        Args:
            care_plan_id: Care plan UUID.
        """
        # Delete tasks first (FK constraint)
        tasks = self.task_repo.get_tasks_by_care_plan(care_plan_id)
        for task in tasks:
            self.task_repo.delete_task(task.task_id)

        # Delete care plan
        self.care_plan_repo.delete(care_plan_id)
        logger.info(f"Deleted care plan {care_plan_id} and {len(tasks)} tasks")

    def refine_task_with_ai(
        self,
        task_id: UUID,
        patient_feedback: str,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Refine a specific task using AI based on patient feedback.

        Args:
            task_id: Task UUID.
            patient_feedback: Feedback text from patient.
            current_user: Current user.

        Returns:
            Refined task data.

        Raises:
            CustomException: If task not found or unauthorized.
        """
        # Get task
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            raise CustomException(http_code=404, code='404', message='Task not found')

        # Verify ownership
        care_plan = self.care_plan_repo.get_by_id(task.care_plan_id)
        if care_plan.patient_id != current_user.user_id and care_plan.caretaker_id != current_user.user_id:
            raise CustomException(http_code=403, code='403', message='Unauthorized access to task')

        # Build task dict for AI
        task_dict = {
            'title': task.title,
            'description': task.description,
            'task_type': task.task_type,
            'task_id': str(task.task_id)
        }

        # Call AI to refine
        refined_task = self.ai_agent.refine_task(task_dict, patient_feedback)

        # Update task in database
        task.title = refined_task.get('title', task.title)
        task.description = refined_task.get('description', task.description)
        updated_task = self.task_repo.update_task(task)

        logger.info(f"Refined task {task_id} based on feedback")

        return {
            'task_id': str(updated_task.task_id),
            'title': updated_task.title,
            'description': updated_task.description,
            'refined_at': datetime.now().isoformat()
        }
