# Care Plan API

Base router: `/care-plans`

## POST /care-plans/generate
- **Auth**: CARETAKER only; must have an assigned patient.
- **Body**:
  - `plan_duration_days` (int, 1–30, default 7)
  - `regenerate` (bool, default false)
- **Business flow**:
  1. Resolve caretaker → assigned patient.
  2. Load patient profile (+ physical therapy detail if applicable).
  3. Load medication, nutrition, exercise libraries.
  4. Call AI to propose tasks.
  5. Validate every AI task must reference an existing library ID; drop invalid; fail 422 if none valid.
  6. If regenerate=true and a plan exists, cascade delete existing plan.
  7. Create `care_plan` and tasks bound to library IDs.
- **Success (200)**: `{ care_plan_id, patient_id, caretaker_id, plan_duration_days, total_tasks, tasks_created, recommendations, generated_at }`
- **Errors**: 400 (plan exists and regenerate=false, bad input), 403 (role), 404 (no patient assigned or missing profile), 422 (AI tasks invalid), 500 (unexpected).

## GET /care-plans/summary
- **Auth**: PATIENT (self) or CARETAKER (assigned patient).
- **Flow**: Resolve patient_id by role → fetch summary.
- **Success (200)**: Care plan summary with task stats.
- **Errors**: 403 (role), 404 (no assigned patient or plan missing), 500.

## POST /care-plans/tasks/{task_id}/refine
- **Auth**: PATIENT or CARETAKER owning the task.
- **Path**: `task_id` (UUID)
- **Body**: `patient_feedback` (string, min 10 chars)
- **Flow**: Validate UUID → AI refines description/notes while keeping task type.
- **Success (200)**: Refined task payload.
- **Errors**: 400 (bad UUID), 403 (not owner/role), 404 (task not found), 500.

## DELETE /care-plans/{patient_id}
- **Auth**: CARETAKER; must be assigned to the patient.
- **Path**: `patient_id` (UUID)
- **Flow**: Validate role & assignment → find plan → cascade delete care_plan + tasks.
- **Success (200)**: Confirmation `{ message, patient_id }`.
- **Errors**: 400 (bad UUID), 403 (not caretaker or wrong patient), 404 (plan not found), 500.

## Domain safeguards
- Care plan is unique per patient; regeneration required to replace.
- Patient profile required; physical therapy detail included when present.
- AI tasks must reference valid Medication/Nutrition/Exercise IDs; unsupported types are rejected.
