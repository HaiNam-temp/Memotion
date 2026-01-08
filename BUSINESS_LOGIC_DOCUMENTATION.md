# MEMOTION - Business Logic & Source Code Documentation

## 📋 Mục Lục
1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Cấu Trúc Source Code](#2-cấu-trúc-source-code)
3. [Database Schema](#3-database-schema)
4. [Business Logic Chi Tiết](#4-business-logic-chi-tiết)
5. [API Endpoints](#5-api-endpoints)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Data Flow](#7-data-flow)

---

## 1. Tổng Quan Hệ Thống

**Memotion** là hệ thống quản lý chăm sóc sức khỏe toàn diện cho bệnh nhân (đặc biệt người cao tuổi), hỗ trợ:
- Theo dõi sức khỏe thể chất và tinh thần
- Quản lý lộ trình chăm sóc (Care Plan)
- Nhắc nhở nhiệm vụ: uống thuốc, dinh dưỡng, tập luyện
- Thông báo và giao tiếp giữa Bệnh nhân - Người chăm sóc

### Vai Trò Người Dùng
- **PATIENT** (Bệnh nhân): Người được chăm sóc
- **CARETAKER** (Người chăm sóc): Gia đình, y tá, điều dưỡng

### Công Nghệ Stack
- **Backend**: FastAPI (Python 3.10)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 1.4.x
- **Authentication**: JWT (JSON Web Token)
- **Validation**: Pydantic
- **Containerization**: Docker

---

## 2. Cấu Trúc Source Code

Dự án tuân theo **Clean Architecture** và **Layered Architecture Pattern**:

```
app/
├── api/                    # 🌐 Presentation Layer (HTTP Endpoints)
│   ├── api_auth.py         # Authentication: Login, Register
│   ├── api_user.py         # User management
│   ├── api_patient_profile.py  # Patient profile CRUD
│   ├── api_task.py         # Task management
│   ├── api_notification.py # Notification system
│   ├── api_medication_library.py  # Medication library
│   ├── api_nutrition_library.py   # Nutrition library
│   ├── api_exercise_library.py    # Exercise library
│   ├── api_upload.py       # File upload
│   ├── api_healthcheck.py  # Health check endpoint
│   └── api_router.py       # Central router configuration
│
├── services/               # 💼 Business Logic Layer
│   ├── srv_user.py         # User business logic
│   ├── srv_patient_profile.py  # Patient profile logic
│   ├── srv_task.py         # Task management logic
│   └── srv_notification.py # Notification logic
│
├── repository/             # 🗄️ Data Access Layer
│   ├── repo_user.py        # User database queries
│   ├── repo_patient_profile.py
│   ├── repo_task.py
│   └── repo_notification.py
│
├── models/                 # 🏗️ Database Models (SQLAlchemy)
│   ├── model_user.py
│   ├── model_patient_profile.py
│   ├── model_care_plan.py
│   ├── model_task.py
│   ├── model_notification.py
│   ├── model_medication_library.py
│   ├── model_nutrition_library.py
│   └── model_exercise_library.py
│
├── schemas/                # 📋 Data Transfer Objects (Pydantic)
│   ├── sche_user.py        # User request/response schemas
│   ├── sche_patient_profile.py
│   ├── sche_task.py
│   ├── sche_notification.py
│   ├── sche_token.py       # JWT token schemas
│   └── sche_base.py        # Base response format
│
├── core/                   # ⚙️ Core Configuration
│   ├── config.py           # Environment settings
│   └── security.py         # Password hashing, JWT generation
│
├── helpers/                # 🔧 Utilities
│   ├── enums.py            # Enums (UserRole, Gender, DiseaseType)
│   ├── exception_handler.py # Custom exception handling
│   ├── login_manager.py    # Login decorator
│   └── paging.py           # Pagination helper
│
├── db/                     # 🔌 Database Connection
│   └── base.py             # SQLAlchemy engine & session
│
└── main.py                 # 🚀 Application Entry Point
```

### Layer Responsibilities

| Layer | Trách Nhiệm | Không Được |
|-------|-------------|-----------|
| **API** | Nhận HTTP request, validate input, gọi Service, trả response | Chứa business logic, query trực tiếp DB |
| **Service** | Xử lý business logic, orchestrate data flow | Biết về HTTP, trả HTTPException |
| **Repository** | Query database, CRUD operations | Chứa business logic |
| **Models** | Định nghĩa cấu trúc bảng | Chứa business logic |
| **Schemas** | Validate & serialize data | Logic xử lý |

---

## 3. Database Schema

### 3.1 Core Tables

#### **users** - Bảng Người Dùng
```sql
users (
  user_id UUID PRIMARY KEY,
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  role VARCHAR(20) NOT NULL,  -- PATIENT | CARETAKER
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP
)
```

#### **patient_caretaker** - Quan Hệ 1-1
```sql
patient_caretaker (
  patient_id UUID FOREIGN KEY users(user_id),
  caretaker_id UUID FOREIGN KEY users(user_id),
  PRIMARY KEY (patient_id, caretaker_id)
)
```

#### **patient_profile** - Hồ Sơ Bệnh Nhân
```sql
patient_profile (
  profile_id UUID PRIMARY KEY,
  patient_id UUID UNIQUE FOREIGN KEY users(user_id),
  gender VARCHAR(255),
  living_arrangement VARCHAR(255),
  bmi_score INTEGER,
  map_score INTEGER,  -- Mean Arterial Pressure
  rhr_score INTEGER,  -- Resting Heart Rate
  adl_score INTEGER,  -- Activities of Daily Living
  iadl_score INTEGER, -- Instrumental ADL
  blood_glucose_level INTEGER,
  disease_type VARCHAR(100) NOT NULL,  -- PHYSICAL_THERAPY | MENTAL_DECLINE | LONELINESS
  condition_note TEXT,
  updated_at TIMESTAMP
)
```

#### **patient_physical_therapy** - Chi Tiết Vật Lý Trị Liệu
```sql
patient_physical_therapy (
  therapy_id UUID PRIMARY KEY,
  profile_id UUID FOREIGN KEY patient_profile(profile_id),
  pain_location TEXT,
  pain_scale_score INTEGER,  -- VAS Score (0-10)
  pain_character VARCHAR(255),
  pain_assessment TEXT,
  muscle_tone VARCHAR(255),
  muscle_strength VARCHAR(255),
  balanced_valuation TEXT,
  fall_risk VARCHAR(255),
  self_stand_ability VARCHAR(255),
  tug_time FLOAT,  -- Timed Up and Go test (seconds)
  previous_illness TEXT,
  previous_treatments TEXT,
  daily_actities TEXT,
  doctor_recommended TEXT,
  doctor_treatment_plan TEXT,
  note TEXT
)
```

### 3.2 Care Plan & Tasks

#### **care_plan** - Kế Hoạch Chăm Sóc
```sql
care_plan (
  care_plan_id UUID PRIMARY KEY,
  patient_id UUID UNIQUE FOREIGN KEY users(user_id),
  caretaker_id UUID FOREIGN KEY users(user_id),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

#### **task** - Nhiệm Vụ
```sql
task (
  task_id UUID PRIMARY KEY,
  care_plan_id UUID FOREIGN KEY care_plan(care_plan_id),
  owner_type VARCHAR(20) NOT NULL,  -- PATIENT | CARETAKER
  title VARCHAR(255) NOT NULL,
  description TEXT,
  task_duedate TIMESTAMP NOT NULL,
  task_type VARCHAR(20) NOT NULL,  -- MEDICATION | NUTRITION | EXERCISE | GENERAL
  medication_id UUID FOREIGN KEY medication_library(medication_id),
  nutrition_id UUID FOREIGN KEY nutrition_library(nutrition_id),
  exercise_id UUID FOREIGN KEY exercise_library(exercise_id),
  status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING | DONE | CANCELLED
  linked_task_id UUID FOREIGN KEY task(task_id)  -- Link to related task
)
```

### 3.3 Library Tables

#### **medication_library** - Thư Viện Thuốc
```sql
medication_library (
  medication_id UUID PRIMARY KEY,
  name VARCHAR(255),
  description TEXT,
  dosage VARCHAR(255),  -- e.g., "500mg"
  frequency_per_day INTEGER,
  notes TEXT,
  image_path VARCHAR(255)
)
```

#### **nutrition_library** - Thư Viện Dinh Dưỡng
```sql
nutrition_library (
  nutrition_id UUID PRIMARY KEY,
  name VARCHAR(255),
  calories INTEGER,
  description TEXT,
  meal_type VARCHAR(50),  -- BREAKFAST | LUNCH | DINNER | SNACK
  image_path VARCHAR(255)
)
```

#### **exercise_library** - Thư Viện Bài Tập
```sql
exercise_library (
  exercise_id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  target_body_region VARCHAR(255),
  description TEXT,
  duration_minutes INTEGER,
  difficulty_level INTEGER,  -- 1-5
  video_path VARCHAR(255)
)
```

### 3.4 Notification System

#### **notification** - Thông Báo
```sql
notification (
  notification_id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY users(user_id),
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  task_id UUID FOREIGN KEY task(task_id),
  type VARCHAR(50) NOT NULL,  -- TASK_REMINDER | SYSTEM | ALERT
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMP
)
```

---

## 4. Business Logic Chi Tiết

### 4.1 User Management

#### Đăng Ký (Registration)
**Service**: `UserService.register_user()`

**Flow**:
1. **Validate Input**: Check email, phone không trùng
2. **Hash Password**: Sử dụng bcrypt
3. **Create User**: Insert vào bảng `users`
4. **Special Case - CARETAKER**:
   - Nếu role = CARETAKER, yêu cầu thông tin Patient
   - Tự động tạo tài khoản Patient liên kết
   - Tạo record trong `patient_caretaker` (quan hệ 1-1)
   - Cả 2 tài khoản dùng chung password ban đầu
5. **Return**: User object (với patient info nếu là caretaker)

**Business Rules**:
- Email phải unique trong toàn hệ thống
- Phone phải unique (nếu cung cấp)
- Caretaker phải cung cấp: `patient_email`, `patient_full_name`
- Password tự động hash trước khi lưu

#### Đăng Nhập (Login)
**Service**: `UserService.authenticate()`

**Flow**:
1. Tìm user theo email
2. Verify password hash
3. Kiểm tra `is_active = true`
4. Generate JWT token (expire: 7 days)
5. Return token

**JWT Payload**:
```json
{
  "user_id": "uuid-string",
  "exp": 1234567890  // Expiration timestamp
}
```

#### Get Current User
**Service**: `UserService.get_current_user()` (Static Method)

**Flow**:
1. Extract JWT từ Authorization header
2. Decode & validate token
3. Query user từ database
4. Return user object

**Used By**: `@login_required` decorator cho các protected endpoints

---

### 4.2 Patient Profile Management

#### Tạo Hồ Sơ Bệnh Nhân
**Service**: `PatientProfileService.create_patient_profile()`

**Flow**:
1. **Authorization**: Chỉ PATIENT role mới tạo được
2. **Check Exist**: Mỗi patient chỉ có 1 profile
3. **Create Profile**: Insert vào `patient_profile`
4. **Disease Type**: Lưu loại bệnh chính

**Business Rules**:
- 1 Patient = 1 Profile (unique constraint)
- Các score (BMI, MAP, RHR, ADL, IADL) là optional
- `disease_type` là required (PHYSICAL_THERAPY | MENTAL_DECLINE | LONELINESS)

#### Tạo Chi Tiết Vật Lý Trị Liệu
**Service**: `PatientProfileService.create_physical_therapy_profile()`

**Flow**:
1. **Check Profile Exists**: Phải có patient_profile trước
2. **Validate Disease Type**: Chỉ áp dụng cho `disease_type = PHYSICAL_THERAPY`
3. **Check Duplicate**: 1 profile chỉ có 1 physical therapy record
4. **Create**: Insert vào `patient_physical_therapy`

**Business Rules**:
- Phải tạo general profile trước
- Chỉ dành cho bệnh nhân vật lý trị liệu
- Các thông số như `pain_scale_score`, `tug_time` dùng để đánh giá tiến triển

#### Update Profile
**Service**: `PatientProfileService.update_patient_profile()`

**Flow**:
1. Get existing profile
2. Update chỉ các field được gửi (partial update)
3. Tự động update `updated_at` timestamp
4. Return updated profile

---

### 4.3 Task Management

#### Lấy Nhiệm Vụ Theo Ngày (Patient)
**Service**: `TaskService.get_patient_tasks_by_date()`

**Flow**:
1. **Get Care Plan**: Tìm care_plan của patient
2. **Query Tasks**: Lấy tasks có `task_duedate` = date input
3. **Filter**: Chỉ lấy tasks có `owner_type = PATIENT`
4. **Return**: List of tasks

**Use Case**: Patient xem công việc cần làm hôm nay

#### Lấy Chi Tiết Task
**Service**: `TaskService.get_task_detail()`

**Flow**:
1. **Get Task**: Query task by ID
2. **Authorization Check**: Task phải thuộc care_plan của user
3. **Load Related Data**:
   - Nếu `task_type = MEDICATION`: Join medication_library
   - Nếu `task_type = NUTRITION`: Join nutrition_library
   - Nếu `task_type = EXERCISE`: Join exercise_library
4. **Return**: Task với full detail

**Response Structure**:
```json
{
  "task_id": "uuid",
  "title": "Uống thuốc Paracetamol",
  "task_type": "MEDICATION",
  "status": "PENDING",
  "task_duedate": "2026-01-07T08:00:00",
  "medication_detail": {
    "name": "Paracetamol",
    "dosage": "500mg",
    "frequency_per_day": 3
  }
}
```

#### Lấy Danh Sách Task (Caretaker)
**Service**: `TaskService.get_caretaker_tasks_with_linked_info()`

**Flow**:
1. **Authorization**: Chỉ CARETAKER role
2. **Get Patient**: Tìm patient được assign cho caretaker
3. **Get Care Plan**: Lấy care_plan của patient
4. **Query Tasks**: Lấy tất cả tasks trong care_plan
5. **Load Linked Tasks**: Nếu có `linked_task_id`, load task liên kết
6. **Return**: List of tasks with linked info

**Use Case**: Caretaker theo dõi toàn bộ nhiệm vụ của patient

#### Hoàn Thành Task
**Service**: `TaskService.complete_task()`

**Flow**:
1. **Authorization**: Chỉ PATIENT role
2. **Get Task**: Query task by ID
3. **Ownership Check**: Task phải thuộc care_plan của patient
4. **Update Status**: Set `status = DONE`
5. **Save**: Commit to database

**Business Rules**:
- Chỉ patient mới được đánh dấu task của mình là hoàn thành
- Caretaker không được complete task của patient (theo design hiện tại)

---

### 4.4 Notification System

#### Lấy Thông Báo
**Service**: `NotificationService.get_user_notifications()`

**Flow**:
1. Query all notifications của user
2. Order by `created_at DESC` (mới nhất trước)
3. Include related task info (nếu có)
4. Return list

**Notification Types**:
- `TASK_REMINDER`: Nhắc nhở làm task
- `SYSTEM`: Thông báo hệ thống
- `ALERT`: Cảnh báo quan trọng

**Business Logic**:
- Notification có thể link với task (optional)
- `is_read` flag để track đã đọc chưa
- Không tự động xóa notification cũ (cần implement cleanup job)

---

### 4.5 Library Management

#### Medication Library
**Purpose**: Quản lý danh mục thuốc có sẵn trong hệ thống

**Key Fields**:
- `name`: Tên thuốc
- `dosage`: Liều lượng (e.g., "500mg", "2 viên")
- `frequency_per_day`: Số lần uống/ngày
- `image_path`: Ảnh minh họa

**Use Case**: Khi tạo task MEDICATION, chọn thuốc từ library thay vì nhập tay

#### Nutrition Library
**Purpose**: Quản lý thực đơn dinh dưỡng

**Key Fields**:
- `meal_type`: BREAKFAST, LUNCH, DINNER, SNACK
- `calories`: Số calo
- `description`: Mô tả món ăn

**Use Case**: Tạo task NUTRITION với món ăn gợi ý

#### Exercise Library
**Purpose**: Quản lý bài tập vật lý trị liệu

**Key Fields**:
- `target_body_region`: Vùng cơ thể (e.g., "Cột sống", "Đầu gối")
- `duration_minutes`: Thời gian tập
- `difficulty_level`: Mức độ khó (1-5)
- `video_path`: Video hướng dẫn

**Use Case**: Assign bài tập cho patient dựa trên tình trạng sức khỏe

---

## 5. API Endpoints

### 5.1 Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/login` | Đăng nhập, nhận JWT token | ❌ |
| POST | `/api/auth/register` | Đăng ký tài khoản mới | ❌ |

**Login Request**:
```json
{
  "username": "patient@example.com",
  "password": "secret123"
}
```

**Login Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Register Request (Patient)**:
```json
{
  "full_name": "Nguyen Van A",
  "email": "patient@example.com",
  "password": "secret123",
  "phone": "0901234567",
  "role": "PATIENT"
}
```

**Register Request (Caretaker)**:
```json
{
  "full_name": "Nguyen Thi B",
  "email": "caretaker@example.com",
  "password": "secret123",
  "phone": "0907654321",
  "role": "CARETAKER",
  "patient_email": "patient@example.com",
  "patient_full_name": "Nguyen Van A",
  "patient_phone": "0901234567"
}
```

### 5.2 User Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/users/me` | Lấy thông tin user hiện tại | ✅ |
| PUT | `/api/users/me` | Cập nhật thông tin user | ✅ |
| GET | `/api/users/{user_id}` | Lấy thông tin user theo ID | ✅ |
| GET | `/api/users` | Lấy danh sách users | ✅ |

### 5.3 Patient Profile

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/patient-profiles` | Tạo hồ sơ bệnh nhân | ✅ PATIENT |
| GET | `/api/patient-profiles/me` | Xem hồ sơ của mình | ✅ PATIENT |
| PUT | `/api/patient-profiles/me` | Cập nhật hồ sơ | ✅ PATIENT |
| POST | `/api/patient-profiles/physical-therapy` | Tạo hồ sơ vật lý trị liệu | ✅ PATIENT |
| GET | `/api/patient-profiles/physical-therapy/me` | Xem chi tiết VLTL | ✅ PATIENT |
| PUT | `/api/patient-profiles/physical-therapy/me` | Cập nhật chi tiết VLTL | ✅ PATIENT |

### 5.4 Tasks

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/tasks/{task_id}` | Lấy chi tiết task | ✅ |
| GET | `/api/tasks/patient/by-date?date=2026-01-07` | Tasks của patient theo ngày | ✅ PATIENT |
| GET | `/api/tasks/patient/medications?date=2026-01-07` | Tasks uống thuốc theo ngày | ✅ PATIENT |
| GET | `/api/tasks/caretaker` | Tất cả tasks (for caretaker) | ✅ CARETAKER |
| GET | `/api/tasks/caretaker/with-linked` | Tasks + linked tasks | ✅ CARETAKER |
| PUT | `/api/tasks/{task_id}/complete` | Đánh dấu task hoàn thành | ✅ PATIENT |

### 5.5 Notifications

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/notifications` | Lấy danh sách thông báo | ✅ |

### 5.6 Libraries

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/medication-library` | Danh sách thuốc | ✅ |
| GET | `/api/nutrition-library` | Danh sách món ăn | ✅ |
| GET | `/api/exercise-library` | Danh sách bài tập | ✅ |

### 5.7 Other

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/healthcheck` | Kiểm tra server status | ❌ |
| POST | `/api/upload` | Upload file (ảnh, video) | ✅ |

---

## 6. Authentication & Authorization

### 6.1 JWT Token Flow

```
Client                    API                     Database
  |                       |                          |
  |-- POST /auth/login -->|                          |
  |                       |-- Query user by email -->|
  |                       |<-- User object ----------|
  |                       |-- Verify password        |
  |                       |-- Generate JWT token     |
  |<-- JWT token ---------|                          |
  |                       |                          |
  |-- GET /tasks/me ----->|                          |
  |   Header: Bearer JWT  |                          |
  |                       |-- Decode JWT             |
  |                       |-- Extract user_id        |
  |                       |-- Query user ----------->|
  |                       |<-- User object ----------|
  |                       |-- Check permissions      |
  |                       |-- Query tasks ---------->|
  |                       |<-- Tasks ----------------|
  |<-- Task list ---------|                          |
```

### 6.2 Protected Endpoints

**Decorator**: `@login_required` (in `app/helpers/login_manager.py`)

**How it works**:
1. Extract `Authorization` header
2. Validate JWT token format
3. Decode token to get `user_id`
4. Query user from database
5. Inject `current_user` vào function parameter

**Example**:
```python
@router.get("/me")
@login_required
def get_my_profile(current_user: User = None):
    # current_user is automatically injected
    return current_user
```

### 6.3 Role-Based Access Control (RBAC)

**Implementation**: Checked inside Service layer

**Example**:
```python
def get_caretaker_tasks(self, current_user: User):
    if current_user.role != UserRole.CARETAKER.value:
        raise Exception("Access denied. Only caretakers can access this.")
    # ... rest of logic
```

**Design Decision**:
- Không dùng decorator cho role check (để linh hoạt)
- Business logic quyết định quyền truy cập
- Throw `Exception` hoặc `CustomException` khi unauthorized

---

## 7. Data Flow

### 7.1 Complete Task Flow

```
Patient (Mobile App)
       |
       | PUT /api/tasks/{task_id}/complete
       v
API Layer (api_task.py)
       |
       | Validate JWT, Extract current_user
       v
Service Layer (srv_task.py)
       |
       | 1. Check user is PATIENT
       | 2. Get task from repository
       | 3. Verify ownership (task belongs to patient's care plan)
       | 4. Update task status to DONE
       v
Repository Layer (repo_task.py)
       |
       | UPDATE task SET status = 'DONE' WHERE task_id = ?
       v
Database (PostgreSQL)
       |
       | Commit transaction
       v
Response back to Client
       |
       | { "success": true, "data": {...} }
```

### 7.2 Register Caretaker Flow

```
Frontend
       |
       | POST /api/auth/register
       | Body: { role: "CARETAKER", patient_email: "...", ... }
       v
API Layer (api_auth.py)
       |
       v
Service Layer (srv_user.py)
       |
       | 1. Validate email uniqueness
       | 2. Hash password
       | 3. Create Caretaker user
       | 4. Create Patient user (auto-linked)
       | 5. Create patient_caretaker relationship
       v
Repository Layer (repo_user.py)
       |
       | INSERT INTO users ... (caretaker)
       | INSERT INTO users ... (patient)
       | INSERT INTO patient_caretaker ...
       v
Database
       |
       | Transaction commit
       v
Response
       |
       | { "success": true, "data": { caretaker, patient } }
```

### 7.3 Get Task Detail with Library Data

```
Client
       |
       | GET /api/tasks/{task_id}
       v
API Layer
       |
       v
Service Layer (srv_task.py)
       |
       | 1. Get task from repo
       | 2. Check task ownership
       | 3. Identify task_type
       | 4. If MEDICATION: Load medication_library data
       | 5. If NUTRITION: Load nutrition_library data
       | 6. If EXERCISE: Load exercise_library data
       v
Repository Layer (repo_task.py)
       |
       | SELECT * FROM task WHERE task_id = ?
       | SELECT * FROM medication_library WHERE medication_id = ?
       v
Database
       |
       | Return task + related library data
       v
Response
       |
       | {
       |   "task_id": "...",
       |   "task_type": "MEDICATION",
       |   "medication_detail": {
       |     "name": "Paracetamol",
       |     "dosage": "500mg"
       |   }
       | }
```

---

## 8. Error Handling

### 8.1 Custom Exception

**Class**: `CustomException` (in `app/helpers/exception_handler.py`)

**Structure**:
```python
class CustomException(Exception):
    http_code: int
    code: str
    message: str
```

**Usage**:
```python
raise CustomException(
    http_code=404,
    code='404',
    message='User not found'
)
```

### 8.2 Standard Response Format

**Success**:
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

**Error**:
```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

**Implementation**: All APIs return `DataResponse[T]` from `app/schemas/sche_base.py`

---

## 9. Database Transactions

### 9.1 Session Management

**Engine**: Created in `app/db/base.py`
```python
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**Session Injection**: Via `fastapi_sqlalchemy` middleware
```python
application.add_middleware(DBSessionMiddleware, db_url=settings.DATABASE_URL)
```

**Usage in Repository**:
```python
from fastapi_sqlalchemy import db

class UserRepository:
    def create(self, user: User):
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user
```

### 9.2 Transaction Boundaries

**Strategy**: Service layer controls transactions

**Pattern**:
- Repository chỉ thực hiện query đơn lẻ
- Service gọi nhiều repository và commit 1 lần
- Nếu có exception, auto rollback

---

## 10. Security Best Practices

### 10.1 Password Security
- **Hashing**: bcrypt via `passlib`
- **Salt**: Tự động generate bởi bcrypt
- **Never log**: Password không được log hoặc return trong response

### 10.2 JWT Security
- **Secret Key**: Lưu trong environment variable
- **Expiration**: 7 days default
- **Algorithm**: HS256
- **Validation**: Verify signature + expiration trong mọi protected endpoint

### 10.3 SQL Injection Prevention
- **ORM**: Sử dụng SQLAlchemy (parameterized queries)
- **No raw SQL**: Tránh `db.execute(f"SELECT * FROM users WHERE email = '{email}'")`

### 10.4 Input Validation
- **Pydantic Schemas**: Validate tất cả input tại API layer
- **Email Format**: Dùng `EmailStr` type
- **UUID Validation**: Tự động validate UUID format

---

## 11. Logging

### 11.1 Log Configuration
**File**: `logging.ini`

**Log Levels**:
- `INFO`: Request/Response tracking
- `ERROR`: Exception với stack trace
- `DEBUG`: Chi tiết xử lý (disable trong production)

### 11.2 Log Format Example
```python
import logging
logger = logging.getLogger(__name__)

# Request log
logger.info(f"register_user request: email={data.email}, role={data.role}")

# Success log
logger.info(f"User registered successfully: user_id={user.user_id}")

# Error log
logger.error(f"Failed to register user: {str(e)}", exc_info=True)
```

---

## 12. Performance Considerations

### 12.1 Database Queries
- **Eager Loading**: Sử dụng `lazy="joined"` cho relationships thường dùng
  ```python
  medication = relationship("MedicationLibrary", lazy="joined")
  ```
- **Avoid N+1**: Load related data trong 1 query thay vì loop

### 12.2 Connection Pooling
- **SQLAlchemy Pool**: Default pool size
- **pool_pre_ping**: Check connection trước khi dùng (handle stale connections)

---

## 13. Deployment

### 13.1 Docker Configuration

**Dockerfile** (Multi-stage build):
```dockerfile
# Stage 1: Build dependencies
FROM python:3.10-slim AS builder
# ... compile wheels

# Stage 2: Runtime
FROM python:3.10-slim
# ... install from wheels
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
```

**docker-compose.yml**:
```yaml
services:
  db:
    image: postgres:15-alpine
    ports: ["5333:5432"]
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: memotion_db

  backend:
    build: .
    ports: ["8005:8005"]
    environment:
      SQL_DATABASE_URL: postgresql://postgres:postgres@db:5432/memotion_db
    depends_on:
      db:
        condition: service_healthy
```

### 13.2 Environment Variables

**Required**:
- `SQL_DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `PROJECT_NAME`: Application name

**Optional**:
- `ACCESS_TOKEN_EXPIRE_SECONDS`: Token expiration (default 7 days)

---

## 14. Testing Strategy

### 14.1 Unit Tests
- Test Service layer logic independently
- Mock Repository layer
- Framework: pytest

### 14.2 Integration Tests
- Test API endpoints end-to-end
- Use test database
- Framework: pytest + FastAPI TestClient

---

## 15. Future Improvements

### 15.1 Planned Features
- [ ] WebSocket cho real-time notifications
- [ ] Chatbot AI integration
- [ ] Daily health tracking (blood pressure, glucose monitoring)
- [ ] Report generation (PDF export)
- [ ] Multi-language support

### 15.2 Technical Debt
- [ ] Implement proper pagination for list endpoints
- [ ] Add API rate limiting
- [ ] Enhance logging with request ID tracking
- [ ] Implement soft delete for users
- [ ] Add database migration with Alembic
- [ ] Improve error messages with error codes catalog

---

## 16. Contact & Maintenance

**Project**: Memotion Healthcare System  
**Version**: 1.0.0  
**Last Updated**: January 2026  
**Documentation**: See `PROJECT_STRUCTURE.md` for architecture guidelines

**Development Team**:
- Backend: FastAPI + PostgreSQL
- Frontend: (Mobile App integration pending)
- DevOps: Docker + GitHub Actions CI/CD

---

*Tài liệu này mô tả chi tiết business logic và cấu trúc source code của hệ thống Memotion. Vui lòng cập nhật khi có thay đổi.*
