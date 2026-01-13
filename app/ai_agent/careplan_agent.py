"""
CarePlan AI Agent for generating personalized care plans.
Uses Gemini API to create medication, nutrition, exercise, and general tasks.
"""
import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.ai_agent.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class CarePlanAgent:
    """
    AI Agent for generating personalized care plans for elderly patients.
    Analyzes patient profile and generates structured task recommendations.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize CarePlan Agent.

        Args:
            gemini_client: GeminiClient instance. If None, creates a new one.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.prompt_template = self._load_prompt_template()
        logger.info("CarePlanAgent initialized")

    def _load_prompt_template(self) -> str:
        """
        Load prompt template from file.

        Returns:
            Prompt template string.
        """
        try:
            prompt_path = os.path.join(
                os.path.dirname(__file__),
                "prompts",
                "careplan_prompt.txt"
            )
            with open(prompt_path, 'r', encoding='utf-8') as f:
                template = f.read()
            logger.info("Loaded prompt template successfully")
            return template
        except Exception as e:
            logger.error(f"Failed to load prompt template: {str(e)}")
            # Return fallback template
            return self._get_fallback_template()

    def _get_fallback_template(self) -> str:
        """Fallback prompt template if file loading fails."""
        return """
You are a healthcare AI assistant specializing in elderly care.
Generate a personalized care plan based on the patient's profile.

Patient Information:
{patient_info}

Available Resources:
{available_resources}

Generate a care plan with tasks in JSON format:
{{
  "tasks": [
    {{
      "owner_type": "PATIENT",
      "title": "Task title",
      "description": "Detailed description",
      "task_type": "MEDICATION|NUTRITION|EXERCISE|GENERAL",
      "resource_id": "UUID from library (if applicable)",
      "schedule_time": "HH:MM",
      "priority": "HIGH|MEDIUM|LOW",
      "notes": "Additional notes"
    }}
  ],
  "recommendations": [
    "Overall recommendation 1",
    "Overall recommendation 2"
  ]
}}

Guidelines:
- Only use resources from the provided libraries
- Prioritize patient safety (low fall risk exercises)
- Consider patient's disease type and severity
- Schedule tasks at appropriate times throughout the day
- Include both patient and caretaker tasks where needed
"""

    def generate_care_plan(
        self,
        patient_profile: Dict[str, Any],
        patient_therapy_detail: Optional[Dict[str, Any]],
        medication_library: List[Dict[str, Any]],
        nutrition_library: List[Dict[str, Any]],
        exercise_library: List[Dict[str, Any]],
        plan_duration_days: int = 7,
        current_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive care plan for a patient.

        Args:
            patient_profile: Patient general profile data.
            patient_therapy_detail: Detailed therapy information (physical/mental/loneliness).
            medication_library: Available medications.
            nutrition_library: Available nutrition plans.
            exercise_library: Available exercises.
            plan_duration_days: Duration of the care plan (default: 7 days).
            current_date: Current date for scheduling tasks (default: today).

        Returns:
            Structured care plan with tasks and recommendations.

        Raises:
            Exception: If plan generation fails.
        """
        if current_date is None:
            current_date = datetime.now()

        try:
            logger.info(f"Generating care plan for patient (disease: {patient_profile.get('disease_type')})")

            # Build prompt
            prompt = self._build_prompt(
                patient_profile=patient_profile,
                patient_therapy_detail=patient_therapy_detail,
                medication_library=medication_library,
                nutrition_library=nutrition_library,
                exercise_library=exercise_library,
                plan_duration_days=plan_duration_days,
                current_date=current_date
            )

            # Call Gemini API
            logger.info("Calling Gemini API to generate care plan...")
            response = self.gemini_client.generate_json_content(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for consistent structured output
                max_tokens=16384  # High token limit for complete responses
            )

            # Log the AI generated plan
            logger.info(f"AI generated care plan: {response}")

            # Validate and enrich response
            validated_plan = self._validate_and_enrich_plan(response, plan_duration_days)

            logger.info(f"Successfully generated care plan with {len(validated_plan.get('tasks', []))} tasks")
            logger.info(f"Validated care plan: {json.dumps(validated_plan, indent=2)}")
            return validated_plan

        except Exception as e:
            logger.error(f"Failed to generate care plan: {str(e)}", exc_info=True)
            raise Exception(f"Care plan generation failed: {str(e)}")

    def _build_prompt(
        self,
        patient_profile: Dict[str, Any],
        patient_therapy_detail: Optional[Dict[str, Any]],
        medication_library: List[Dict[str, Any]],
        nutrition_library: List[Dict[str, Any]],
        exercise_library: List[Dict[str, Any]],
        plan_duration_days: int,
        current_date: datetime
    ) -> str:
        """
        Build complete prompt for Gemini API.

        Args:
            patient_profile: Patient profile data.
            patient_therapy_detail: Therapy details.
            medication_library: Medications list.
            nutrition_library: Nutrition list.
            exercise_library: Exercises list.
            plan_duration_days: Plan duration.
            current_date: Current date for scheduling.

        Returns:
            Complete prompt string.
        """
        # Format patient information
        patient_info = self._format_patient_info(patient_profile, patient_therapy_detail)

        # Format available resources
        resources = self._format_available_resources(
            medication_library,
            nutrition_library,
            exercise_library
        )

        # Build final prompt
        prompt = self.prompt_template.format(
            patient_info=patient_info,
            available_resources=resources,
            plan_duration_days=plan_duration_days,
            current_date=current_date.strftime("%Y-%m-%d")
        )

        return prompt

    def _format_patient_info(
        self,
        profile: Dict[str, Any],
        therapy_detail: Optional[Dict[str, Any]]
    ) -> str:
        """Format patient information for prompt."""
        info_parts = [
            f"Gender: {profile.get('gender', 'Unknown')}",
            f"Disease Type: {profile.get('disease_type', 'Unknown')}",
            f"BMI Score: {profile.get('bmi_score', 'N/A')}",
            f"ADL Score: {profile.get('adl_score', 'N/A')}",
            f"IADL Score: {profile.get('iadl_score', 'N/A')}",
            f"Blood Glucose: {profile.get('blood_glucose_level', 'N/A')} mg/dL",
            f"Condition Notes: {profile.get('condition_note', 'None')}"
        ]

        if therapy_detail:
            info_parts.extend([
                "\n--- Therapy Details ---",
                f"Pain Location: {therapy_detail.get('pain_location', 'N/A')}",
                f"Pain Scale (VAS): {therapy_detail.get('pain_scale_score', 'N/A')}/10",
                f"Fall Risk: {therapy_detail.get('fall_risk', 'N/A')}",
                f"Muscle Strength: {therapy_detail.get('muscle_strength', 'N/A')}",
                f"Balance: {therapy_detail.get('balanced_valuation', 'N/A')}",
                f"TUG Time: {therapy_detail.get('tug_time', 'N/A')} seconds",
                f"Doctor's Plan: {therapy_detail.get('doctor_treatment_plan', 'N/A')}"
            ])

        return "\n".join(info_parts)

    def _format_available_resources(
        self,
        medications: List[Dict[str, Any]],
        nutrition: List[Dict[str, Any]],
        exercises: List[Dict[str, Any]]
    ) -> str:
        """Format available resources (libraries) for prompt."""
        parts = []

        # Medications
        parts.append("=== Available Medications ===")
        for med in medications[:10]:  # Limit to top 10
            parts.append(
                f"- ID: {med.get('medication_id')} | "
                f"{med.get('name')} ({med.get('dosage')}) | "
                f"Frequency: {med.get('frequency_per_day', 1)}x/day"
            )

        # Nutrition
        parts.append("\n=== Available Nutrition Plans ===")
        for nut in nutrition[:10]:
            parts.append(
                f"- ID: {nut.get('nutrition_id')} | "
                f"{nut.get('name')} ({nut.get('meal_type')}) | "
                f"Calories: {nut.get('calories')} kcal"
            )

        # Exercises
        parts.append("\n=== Available Exercises ===")
        for ex in exercises[:15]:
            parts.append(
                f"- ID: {ex.get('exercise_id')} | "
                f"{ex.get('name')} | "
                f"Target: {ex.get('target_body_region')} | "
                f"Duration: {ex.get('duration_minutes')} min | "
                f"Difficulty: {ex.get('difficulty_level', 1)}/5"
            )

        return "\n".join(parts)

    def _validate_and_enrich_plan(
        self,
        plan: Dict[str, Any],
        plan_duration_days: int
    ) -> Dict[str, Any]:
        """
        Validate and enrich the generated care plan.

        Args:
            plan: Raw plan from Gemini.
            plan_duration_days: Plan duration.

        Returns:
            Validated and enriched plan.
        """
        if 'task_patterns' not in plan:
            raise ValueError("Generated plan missing 'task_patterns' field")

        task_patterns = plan['task_patterns']
        validated_tasks = []

        for pattern in task_patterns:
            # Validate required fields
            if not pattern.get('title') or not pattern.get('task_type') or not pattern.get('due_dates'):
                logger.warning(f"Skipping invalid task pattern: {pattern}")
                continue

            # Validate resource IDs based on task type
            task_type = pattern['task_type']
            if task_type == 'MEDICATION' and 'medication_id' not in pattern:
                logger.warning(f"Skipping MEDICATION pattern without medication_id: {pattern}")
                continue
            elif task_type == 'NUTRITION' and 'nutrition_id' not in pattern:
                logger.warning(f"Skipping NUTRITION pattern without nutrition_id: {pattern}")
                continue
            elif task_type == 'EXERCISE' and 'exercise_id' not in pattern:
                logger.warning(f"Skipping EXERCISE pattern without exercise_id: {pattern}")
                continue

            # Expand the pattern into individual tasks
            pattern_tasks = self._expand_task_pattern(pattern)
            validated_tasks.extend(pattern_tasks)

        plan['tasks'] = validated_tasks
        plan.setdefault('recommendations', [])
        plan['plan_duration_days'] = plan_duration_days
        plan['generated_at'] = datetime.now().isoformat()

        # Log the validated tasks
        logger.info(f"Validated tasks: {validated_tasks}")
        return plan

    def _expand_task_pattern(
        self,
        pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Expand a task pattern into individual tasks based on due_dates array.

        Args:
            pattern: Task pattern with due_dates array.

        Returns:
            List of individual task dictionaries.
        """
        tasks = []
        due_dates = pattern.get('due_dates', [])

        for due_date_str in due_dates:
            try:
                # Parse the due date
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))

                # Create a task for this due date
                task = {
                    'title': pattern['title'],
                    'description': pattern.get('description', ''),
                    'task_type': pattern['task_type'],
                    'owner_type': pattern.get('owner_type', 'PATIENT'),
                    'priority': pattern.get('priority', 'MEDIUM'),
                    'status': pattern.get('status', 'PENDING'),
                    'task_duedate': due_date_str  # Keep as string for consistency
                }

                # Map resource IDs based on task type - AI should provide correct field names
                task_type = pattern['task_type']
                if task_type == 'MEDICATION' and 'medication_id' in pattern:
                    task['medication_id'] = pattern['medication_id']
                elif task_type == 'NUTRITION' and 'nutrition_id' in pattern:
                    task['nutrition_id'] = pattern['nutrition_id']
                elif task_type == 'EXERCISE' and 'exercise_id' in pattern:
                    task['exercise_id'] = pattern['exercise_id']

                tasks.append(task)

            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid due_date format '{due_date_str}' in pattern {pattern.get('title')}: {e}")
                continue

        logger.info(f"Expanded pattern '{pattern.get('title')}' into {len(tasks)} tasks")
        return tasks

    def refine_task(
        self,
        task: Dict[str, Any],
        patient_feedback: str
    ) -> Dict[str, Any]:
        """
        Refine a specific task based on patient feedback.

        Args:
            task: Original task data.
            patient_feedback: Feedback from patient or caretaker.

        Returns:
            Refined task.
        """
        try:
            prompt = f"""
Refine this healthcare task based on patient feedback.

Original Task:
Title: {task.get('title')}
Description: {task.get('description')}
Type: {task.get('task_type')}

Patient Feedback:
{patient_feedback}

Provide a refined task in JSON format with updated title, description, and notes.
Keep the same task_type and resource_id if present.
            """

            response = self.gemini_client.generate_json_content(prompt, temperature=0.5)

            # Merge with original task
            refined_task = {**task, **response}
            logger.info(f"Task refined based on feedback")
            return refined_task

        except Exception as e:
            logger.error(f"Failed to refine task: {str(e)}")
            return task  # Return original if refinement fails

    def generate_caretaker_tasks(
        self,
        patient_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate caretaker tasks based on patient tasks.
        Each caretaker task supports and monitors the corresponding patient task.

        Args:
            patient_tasks: List of patient task dictionaries.

        Returns:
            List of caretaker task dictionaries.
        """
        try:
            logger.info(f"Generating caretaker tasks for {len(patient_tasks)} patient tasks")

            caretaker_tasks = []

            for patient_task in patient_tasks:
                # Skip if not a patient task
                if patient_task.get('owner_type') != 'PATIENT':
                    continue

                # Generate caretaker task based on patient task
                caretaker_task = self._generate_single_caretaker_task(patient_task)
                if caretaker_task:
                    caretaker_tasks.append(caretaker_task)

            logger.info(f"Generated {len(caretaker_tasks)} caretaker tasks")
            return caretaker_tasks

        except Exception as e:
            logger.error(f"Failed to generate caretaker tasks: {str(e)}", exc_info=True)
            raise Exception(f"Caretaker task generation failed: {str(e)}")

    def _generate_single_caretaker_task(
        self,
        patient_task: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single caretaker task based on a patient task.

        Args:
            patient_task: Patient task dictionary.

        Returns:
            Caretaker task dictionary or None if generation fails.
        """
        try:
            task_type = patient_task.get('task_type')
            title = patient_task.get('title', '')
            description = patient_task.get('description', '')
            task_duedate = patient_task.get('task_duedate')

            # Build caretaker task based on task type
            if task_type == 'MEDICATION':
                caretaker_title = f"Nhắc nhở bệnh nhân uống thuốc: {title}"
                caretaker_description = f"Đảm bảo bệnh nhân uống thuốc đúng lịch. Giám sát việc tuân thủ và cung cấp hỗ trợ nếu cần. {description}"

            elif task_type == 'NUTRITION':
                caretaker_title = f"Hỗ trợ bữa ăn: {title}"
                caretaker_description = f"Giúp chuẩn bị hoặc nhắc nhở bệnh nhân về bữa ăn. Đảm bảo dinh dưỡng đầy đủ. {description}"

            elif task_type == 'EXERCISE':
                caretaker_title = f"Giám sát bài tập: {title}"
                caretaker_description = f"Giám sát và hỗ trợ bệnh nhân trong lúc tập luyện. Đảm bảo an toàn và tư thế đúng. {description}"

            else:  # GENERAL
                caretaker_title = f"Hỗ trợ nhiệm vụ của bệnh nhân: {title}"
                caretaker_description = f"Cung cấp hỗ trợ và giám sát cho hoạt động của bệnh nhân. {description}"

            # Create caretaker task with same resource IDs and due date
            caretaker_task = {
                'owner_type': 'CARETAKER',
                'title': caretaker_title,
                'description': caretaker_description,
                'task_type': task_type,  # Same task type for consistency
                'task_duedate': task_duedate,
                'priority': patient_task.get('priority', 'MEDIUM'),  # Same priority as patient task
                'status': 'PENDING',
                'linked_task_id': patient_task.get('task_id')  # Will be set after patient task is created
            }

            # Copy resource IDs to maintain user logic consistency
            if 'medication_id' in patient_task:
                caretaker_task['medication_id'] = patient_task['medication_id']
            if 'nutrition_id' in patient_task:
                caretaker_task['nutrition_id'] = patient_task['nutrition_id']
            if 'exercise_id' in patient_task:
                caretaker_task['exercise_id'] = patient_task['exercise_id']

            return caretaker_task

        except Exception as e:
            logger.warning(f"Failed to generate caretaker task for patient task {patient_task.get('title')}: {str(e)}")
            return None
