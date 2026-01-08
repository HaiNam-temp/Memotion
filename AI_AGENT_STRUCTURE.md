# Thiết Kế AI CarePlan Agent cho Memotion

Tài liệu này mô tả chi tiết kiến trúc và thiết kế source code cho **AI CarePlan Agent** dùng Gemini API, tích hợp vào hệ thống Memotion (FastAPI + PostgreSQL, kiến trúc Layered/Clean Architecture). Thiết kế bám sát các best practice về service layer pattern và tách biệt domain với hạ tầng. [web:11][web:17]

---

## 1. Mục Tiêu & Phạm Vi

### 1.1. Mục tiêu

- Tự động sinh **CarePlan** cho bệnh nhân (đặc biệt người cao tuổi) dựa trên:
  - Hồ sơ bệnh án tổng quát: `patient_profile`
  - Hồ sơ chi tiết vật lý trị liệu: `patient_physical_therapy`
  - Thư viện chuẩn hóa: `medication_library`, `nutrition_library`, `exercise_library`  
- Sinh ra danh sách **Task** (thuốc, dinh dưỡng, bài tập, general) gắn với `care_plan`, lưu vào bảng `task` của hệ thống.  
- Đảm bảo:
  - Output có cấu trúc rõ ràng, parse được thành domain model.
  - Chỉ dùng các item có sẵn trong thư viện (không bịa thuốc/bài tập).  
  - Logic an toàn cho người cao tuổi (ưu tiên bài tập nhẹ, giảm nguy cơ té ngã). [web:24]

### 1.2. Phạm vi

- Thiết kế **source structure** (thư mục, module).
- Thiết kế **DTO / schema** vào–ra cho agent.
- Thiết kế **prompt + call Gemini**.
- Thiết kế **Service orchestration** tạo CarePlan + Task.
- Thiết kế **API endpoint** để caretaker kích hoạt agent.

---

## 2. Tích Hợp Vào Kiến Trúc Hiện Tại

Project Memotion hiện dùng kiến trúc **Layered Architecture**: API → Service → Repository → DB, với FastAPI, SQLAlchemy, Pydantic. [web:11][web:14]

### 2.1. Cấu trúc thư mục mở rộng

```bash
app/
├── api/
│   ├── api_auth.py
│   ├── api_task.py
│   ├── api_patient_profile.py
│   ├── api_care_plan.py          # NEW: Endpoint sinh CarePlan bằng AI
│   └── ...
├── services/
│   ├── srv_user.py
│   ├── srv_task.py
│   ├── srv_patient_profile.py
│   ├── srv_care_plan.py          # NEW: Orchestrate AI care plan
│   └── ...
├── repository/
│   ├── repo_user.py
│   ├── repo_patient_profile.py
│   ├── repo_task.py
│   ├── repo_care_plan.py
│   ├── repo_medication_library.py
│   ├── repo_nutrition_library.py
│   └── repo_exercise_library.py
├── ai_agent/                      # NEW: Lớp AI agent
│   ├── gemini_client.py          # Kết nối Gemini
│   ├── careplan_agent.py         # Logic tạo CarePlan/Task
│   ├── mappers.py                # Map LLM output → domain
│   └── prompts/
│       └── careplan_prompt.txt   # Prompt hệ thống
└── ...
