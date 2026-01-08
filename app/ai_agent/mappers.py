"""
Mappers for converting LLM output to domain models.
Transforms AI-generated data structures into application domain objects.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

logger = logging.getLogger(__name__)


class CarePlanMapper:
    """
    Maps AI-generated care plan data to domain models compatible with database schema.
    """

    @staticmethod
    def map_ai_plan_to_task_models(
        ai_plan: Dict[str, Any],
        care_plan_id: UUID,
        start_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Convert AI-generated plan to list of Task model dictionaries.

        Args:
            ai_plan: AI-generated care plan with tasks.
            care_plan_id: Care plan UUID to associate tasks with.
            start_date: Start date for scheduling tasks (default: today).

        Returns:
            List of task dictionaries ready for database insertion.
        """
        if start_date is None:
            start_date = datetime.now()

        tasks = ai_plan.get('tasks', [])
        task_models = []

        for idx, ai_task in enumerate(tasks):
            try:
                task_model = CarePlanMapper._map_single_task(
                    ai_task=ai_task,
                    care_plan_id=care_plan_id,
                    start_date=start_date,
                    task_index=idx
                )
                task_models.append(task_model)
            except Exception as e:
                logger.error(f"Failed to map task {idx}: {str(e)}")
                continue

        logger.info(f"Mapped {len(task_models)} tasks from AI plan")
        return task_models

    @staticmethod
    def _map_single_task(
        ai_task: Dict[str, Any],
        care_plan_id: UUID,
        start_date: datetime,
        task_index: int
    ) -> Dict[str, Any]:
        """
        Map a single AI task to database task model.

        Args:
            ai_task: AI-generated task data.
            care_plan_id: Care plan UUID.
            start_date: Base date for scheduling.
            task_index: Index of task in the list.

        Returns:
            Task model dictionary.
        """
        # Check if AI provided task_duedate directly
        if 'task_duedate' in ai_task:
            try:
                task_duedate = datetime.fromisoformat(ai_task['task_duedate'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid task_duedate format: {ai_task['task_duedate']}, falling back to calculation")
                task_duedate = CarePlanMapper._calculate_task_duedate_from_schedule(
                    start_date=start_date,
                    task_index=task_index,
                    task_type=ai_task.get('task_type')
                )
        else:
            # Extract schedule time (HH:MM format) or use default
            schedule_time = ai_task.get('schedule_time', '09:00')
            task_duedate = CarePlanMapper._calculate_task_duedate(
                start_date=start_date,
                schedule_time=schedule_time,
                task_index=task_index,
                task_type=ai_task.get('task_type')
            )

        # Build task model
        task_model = {
            'care_plan_id': care_plan_id,
            'owner_type': ai_task.get('owner_type', 'PATIENT'),
            'title': ai_task['title'],
            'description': ai_task.get('description', ''),
            'task_duedate': task_duedate,
            'task_type': ai_task['task_type'],
            'status': ai_task.get('status', 'PENDING')
        }

        # Map resource IDs based on task type
        try:
            if ai_task['task_type'] == 'MEDICATION' and 'medication_id' in ai_task:
                parsed_id = CarePlanMapper._parse_uuid(ai_task['medication_id'])
                if parsed_id:
                    task_model['medication_id'] = parsed_id
            elif ai_task['task_type'] == 'NUTRITION' and 'nutrition_id' in ai_task:
                parsed_id = CarePlanMapper._parse_uuid(ai_task['nutrition_id'])
                if parsed_id:
                    task_model['nutrition_id'] = parsed_id
            elif ai_task['task_type'] == 'EXERCISE' and 'exercise_id' in ai_task:
                parsed_id = CarePlanMapper._parse_uuid(ai_task['exercise_id'])
                if parsed_id:
                    task_model['exercise_id'] = parsed_id
        except Exception as e:
            logger.warning(f"Error parsing resource ID in task {task_index}: {e}. Skipping resource mapping.")

        # Handle linked_task_id if provided
        if 'linked_task_id' in ai_task and ai_task['linked_task_id']:
            parsed_linked_id = CarePlanMapper._parse_uuid(ai_task['linked_task_id'])
            if parsed_linked_id:
                task_model['linked_task_id'] = parsed_linked_id

        return task_model

    @staticmethod
    def _calculate_task_duedate(
        start_date: datetime,
        schedule_time: str,
        task_index: int,
        task_type: str
    ) -> datetime:
        """
        Calculate task due date based on task type and schedule.

        Args:
            start_date: Base date.
            schedule_time: Time in HH:MM format.
            task_index: Task position in list.
            task_type: Type of task.

        Returns:
            Calculated due date datetime.
        """
        try:
            # Parse schedule time
            hour, minute = map(int, schedule_time.split(':'))

            # Calculate base date (spread tasks across the week)
            if task_type == 'MEDICATION':
                # Medications start from day 0 (today)
                day_offset = 0
            elif task_type == 'NUTRITION':
                # Nutrition tasks cycle through the week
                day_offset = task_index % 7
            elif task_type == 'EXERCISE':
                # Exercises every other day
                day_offset = (task_index * 2) % 7
            else:
                # General tasks spread across week
                day_offset = task_index % 7

            task_date = start_date + timedelta(days=day_offset)
            task_duedate = task_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            return task_duedate

        except Exception as e:
            logger.warning(f"Failed to parse schedule_time '{schedule_time}': {str(e)}")
            # Default to 9 AM on start date
            return start_date.replace(hour=9, minute=0, second=0, microsecond=0)

    @staticmethod
    def _calculate_task_duedate_from_schedule(
        start_date: datetime,
        task_index: int,
        task_type: str
    ) -> datetime:
        """
        Calculate task due date when no specific time is provided.

        Args:
            start_date: Base date.
            task_index: Task position in list.
            task_type: Type of task.

        Returns:
            Calculated due date datetime.
        """
        # Calculate base date (spread tasks across the week)
        if task_type == 'MEDICATION':
            day_offset = 0
        elif task_type == 'NUTRITION':
            day_offset = task_index % 7
        elif task_type == 'EXERCISE':
            day_offset = (task_index * 2) % 7
        else:
            day_offset = task_index % 7

        task_date = start_date + timedelta(days=day_offset)
        # Default to 9 AM
        return task_date.replace(hour=9, minute=0, second=0, microsecond=0)

    @staticmethod
    def _parse_uuid(uuid_string: Any) -> Optional[UUID]:
        """
        Safely parse UUID from string.

        Args:
            uuid_string: UUID as string or UUID object.

        Returns:
            UUID object or None if invalid.
        """
        if isinstance(uuid_string, UUID):
            return uuid_string

        if not uuid_string:
            return None

        try:
            return UUID(str(uuid_string))
        except (ValueError, AttributeError):
            logger.warning(f"Invalid UUID format: {uuid_string}")
            return None


class TaskResponseMapper:
    """
    Maps database task models to API response formats.
    """

    @staticmethod
    def map_task_to_response(task: Any, include_details: bool = True) -> Dict[str, Any]:
        """
        Convert Task model to API response dictionary.

        Args:
            task: Task model object.
            include_details: Whether to include related resource details.

        Returns:
            Task response dictionary.
        """
        response = {
            'task_id': str(task.task_id),
            'care_plan_id': str(task.care_plan_id),
            'owner_type': task.owner_type,
            'title': task.title,
            'description': task.description,
            'task_duedate': task.task_duedate.isoformat() if task.task_duedate else None,
            'task_type': task.task_type,
            'status': task.status
        }

        if include_details:
            # Add medication details
            if task.task_type == 'MEDICATION' and hasattr(task, 'medication') and task.medication:
                response['medication_detail'] = {
                    'medication_id': str(task.medication.medication_id),
                    'name': task.medication.name,
                    'dosage': task.medication.dosage,
                    'frequency_per_day': task.medication.frequency_per_day
                }

            # Add nutrition details
            if task.task_type == 'NUTRITION' and hasattr(task, 'nutrition') and task.nutrition:
                response['nutrition_detail'] = {
                    'nutrition_id': str(task.nutrition.nutrition_id),
                    'name': task.nutrition.name,
                    'calories': task.nutrition.calories,
                    'meal_type': task.nutrition.meal_type
                }

            # Add exercise details
            if task.task_type == 'EXERCISE' and hasattr(task, 'exercise') and task.exercise:
                response['exercise_detail'] = {
                    'exercise_id': str(task.exercise.exercise_id),
                    'name': task.exercise.name,
                    'target_body_region': task.exercise.target_body_region,
                    'duration_minutes': task.exercise.duration_minutes,
                    'difficulty_level': task.exercise.difficulty_level
                }

        return response


class PatientProfileMapper:
    """
    Maps patient profile data to formats suitable for AI agent.
    """

    @staticmethod
    def map_profile_to_ai_input(
        profile: Any,
        therapy_detail: Any = None
    ) -> Dict[str, Any]:
        """
        Convert database profile models to AI agent input format.

        Args:
            profile: PatientProfile model.
            therapy_detail: Therapy detail model (physical/mental/loneliness).

        Returns:
            Dictionary formatted for AI agent consumption.
        """
        profile_dict = {
            'profile_id': str(profile.profile_id),
            'patient_id': str(profile.patient_id),
            'gender': profile.gender,
            'living_arrangement': profile.living_arrangement,
            'bmi_score': profile.bmi_score,
            'map_score': profile.map_score,
            'rhr_score': profile.rhr_score,
            'adl_score': profile.adl_score,
            'iadl_score': profile.iadl_score,
            'blood_glucose_level': profile.blood_glucose_level,
            'disease_type': profile.disease_type,
            'condition_note': profile.condition_note
        }

        if therapy_detail:
            therapy_dict = PatientProfileMapper._map_therapy_detail(therapy_detail)
            profile_dict['therapy_detail'] = therapy_dict

        return profile_dict

    @staticmethod
    def _map_therapy_detail(therapy: Any) -> Dict[str, Any]:
        """Map therapy detail model to dictionary."""
        # Handle different therapy types
        therapy_dict = {}

        # Physical therapy fields
        if hasattr(therapy, 'pain_location'):
            therapy_dict.update({
                'pain_location': therapy.pain_location,
                'pain_scale_score': therapy.pain_scale_score,
                'pain_character': therapy.pain_character,
                'pain_assessment': therapy.pain_assessment,
                'muscle_tone': therapy.muscle_tone,
                'muscle_strength': therapy.muscle_strength,
                'balanced_valuation': therapy.balanced_valuation,
                'fall_risk': therapy.fall_risk,
                'self_stand_ability': therapy.self_stand_ability,
                'tug_time': therapy.tug_time,
                'previous_illness': therapy.previous_illness,
                'previous_treatments': therapy.previous_treatments,
                'daily_actities': therapy.daily_actities,
                'doctor_recommended': therapy.doctor_recommended,
                'doctor_treatment_plan': therapy.doctor_treatment_plan,
                'note': therapy.note
            })

        # Add other therapy type mappings here (mental decline, loneliness)

        return therapy_dict


class LibraryMapper:
    """
    Maps library items (medication, nutrition, exercise) to AI-friendly formats.
    """

    @staticmethod
    def map_medications_to_ai_format(medications: List[Any]) -> List[Dict[str, Any]]:
        """Convert medication models to AI input format."""
        return [
            {
                'medication_id': str(med.medication_id),
                'name': med.name,
                'description': med.description,
                'dosage': med.dosage,
                'frequency_per_day': med.frequency_per_day,
                'notes': med.notes
            }
            for med in medications
        ]

    @staticmethod
    def map_nutrition_to_ai_format(nutrition_items: List[Any]) -> List[Dict[str, Any]]:
        """Convert nutrition models to AI input format."""
        return [
            {
                'nutrition_id': str(nut.nutrition_id),
                'name': nut.name,
                'calories': nut.calories,
                'description': nut.description,
                'meal_type': nut.meal_type
            }
            for nut in nutrition_items
        ]

    @staticmethod
    def map_exercises_to_ai_format(exercises: List[Any]) -> List[Dict[str, Any]]:
        """Convert exercise models to AI input format."""
        return [
            {
                'exercise_id': str(ex.exercise_id),
                'name': ex.name,
                'target_body_region': ex.target_body_region,
                'description': ex.description,
                'duration_minutes': ex.duration_minutes,
                'difficulty_level': ex.difficulty_level
            }
            for ex in exercises
        ]
