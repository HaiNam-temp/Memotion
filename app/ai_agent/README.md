# AI Agent Configuration Guide

## Overview
This guide explains how to configure and use the AI Care Plan Agent in Memotion.

## Setup

### 1. Install Dependencies
```bash
pip install google-generativeai>=0.3.0
```

### 2. Get Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 3. Configure Environment Variable
Add to your `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
```

## API Endpoints

### Generate Care Plan
**POST** `/api/care-plans/generate`

**Authorization**: Bearer token (CARETAKER role required)

**Request Body**:
```json
{
  "plan_duration_days": 7,
  "regenerate": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "care_plan_id": "uuid",
    "patient_id": "uuid",
    "caretaker_id": "uuid",
    "plan_duration_days": 7,
    "total_tasks": 28,
    "tasks_created": 28,
    "recommendations": [
      "Monitor pain levels daily",
      "Encourage hydration"
    ],
    "generated_at": "2026-01-07T10:30:00"
  }
}
```

### Get Care Plan Summary
**GET** `/api/care-plans/summary`

**Authorization**: Bearer token (PATIENT or CARETAKER)

**Response**:
```json
{
  "success": true,
  "data": {
    "care_plan_id": "uuid",
    "task_statistics": {
      "total": 28,
      "pending": 20,
      "done": 8,
      "by_type": {
        "MEDICATION": 12,
        "NUTRITION": 8,
        "EXERCISE": 5,
        "GENERAL": 3
      }
    }
  }
}
```

### Refine Task with AI
**POST** `/api/care-plans/tasks/{task_id}/refine`

**Authorization**: Bearer token (PATIENT or CARETAKER)

**Request Body**:
```json
{
  "patient_feedback": "This exercise is too difficult for me"
}
```

### Delete Care Plan
**DELETE** `/api/care-plans/{patient_id}`

**Authorization**: Bearer token (CARETAKER only)

## Usage Flow

### For Caretakers:
1. Patient registers and creates profile
2. Caretaker logs in
3. Caretaker calls `/api/care-plans/generate`
4. AI generates personalized care plan with tasks
5. Patient sees tasks in their task list
6. Caretaker monitors progress via `/api/care-plans/summary`

### For Patients:
1. View assigned tasks via `/api/tasks/patient/by-date`
2. Complete tasks via `/api/tasks/{task_id}/complete`
3. Request task refinement via `/api/care-plans/tasks/{task_id}/refine`

## Customization

### Modify Prompt Template
Edit file: `app/ai_agent/prompts/careplan_prompt.txt`

### Adjust AI Parameters
In `app/ai_agent/careplan_agent.py`:
```python
response = self.gemini_client.generate_json_content(
    prompt=prompt,
    temperature=0.3,  # Lower = more consistent
    max_tokens=4096
)
```

### Add Custom Validation
Edit `app/ai_agent/mappers.py` -> `CarePlanMapper._validate_and_enrich_plan()`

## Troubleshooting

### Error: "GEMINI_API_KEY not found"
- Check `.env` file has `GEMINI_API_KEY` set
- Restart the application after adding the key

### Error: "Patient profile not found"
- Patient must create their profile first via `/api/patient-profiles`

### Error: "Invalid JSON response from Gemini"
- Try regenerating with `regenerate=true`
- Check prompt template for syntax errors

### Tasks seem inappropriate
- Review prompt template in `careplan_prompt.txt`
- Ensure patient profile data is accurate
- Adjust temperature parameter (lower = more conservative)

## Safety Features

1. **Fall Risk Assessment**: Automatically selects low-difficulty exercises for high-risk patients
2. **Pain Threshold**: Avoids strenuous activities for patients with high pain scores
3. **Resource Validation**: Only uses medications/exercises from approved library
4. **Task Limit**: Caps daily tasks to avoid overwhelming patients

## Performance Tips

1. **Library Size**: Keep libraries under 50 items for faster generation
2. **Caching**: Consider caching library data to reduce DB queries
3. **Async Processing**: For production, consider async task generation
4. **Rate Limiting**: Implement rate limiting on generation endpoint

## Security

- API key stored in environment variable (never in code)
- Authorization enforced on all endpoints
- Caretaker-patient relationship validated before generation
- Task ownership verified before refinement

## Monitoring

Log locations:
- Generation requests: `logger.info("Generating care plan for patient...")`
- AI errors: `logger.error("Failed to generate care plan...")`
- Task creation: `logger.info("Successfully created care plan with X tasks")`

## Future Enhancements

- [ ] Multi-language support in prompts
- [ ] A/B testing different prompt templates
- [ ] User feedback collection on AI suggestions
- [ ] Integration with medical knowledge bases
- [ ] Automated plan adjustment based on progress
