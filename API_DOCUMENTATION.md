# API Documentation - Memotion

## 1. Authentication & User Management

### 1.1. Register User (Đăng ký)

Đăng ký người dùng mới vào hệ thống. Hỗ trợ đăng ký cho 2 vai trò: `PATIENT` (Bệnh nhân) và `CARETAKER` (Người chăm sóc).

*   **URL**: `/api/auth/register`
*   **Method**: `POST`
*   **Content-Type**: `application/json`

#### Request Body

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `full_name` | string | **Yes** | Họ và tên của người đăng ký. |
| `email` | string | **Yes** | Địa chỉ email (dùng để đăng nhập). Phải là duy nhất. |
| `password` | string | **Yes** | Mật khẩu đăng nhập. |
| `phone` | string | No | Số điện thoại của người đăng ký. |
| `role` | string | No | Vai trò người dùng. Giá trị: `PATIENT` hoặc `CARETAKER`. Mặc định là `PATIENT`. |
| `patient_full_name`| string | **Conditional**| **Bắt buộc nếu role là `CARETAKER`**. Họ tên của bệnh nhân mà người này chăm sóc. |
| `patient_email` | string | **Conditional**| **Bắt buộc nếu role là `CARETAKER`**. Email cho tài khoản bệnh nhân (hệ thống sẽ tự tạo tài khoản này). |
| `patient_phone` | string | No | Số điện thoại của bệnh nhân (nếu có). |

#### Logic xử lý đặc biệt cho Role `CARETAKER`

Nếu người dùng đăng ký với vai trò là **CARETAKER**:
1.  Hệ thống sẽ tạo tài khoản cho Caretaker với thông tin `full_name`, `email`, `password`, `phone`.
2.  Hệ thống sẽ **tự động tạo thêm** một tài khoản Patient với thông tin từ các trường `patient_*`.
3.  Tài khoản Patient này sẽ dùng chung mật khẩu với Caretaker (để dễ quản lý ban đầu).
4.  Hệ thống tự động liên kết 2 tài khoản này với nhau (1 Caretaker - 1 Patient).

#### Example Requests

**Trường hợp 1: Đăng ký là Bệnh nhân (Patient)**

```json
{
  "full_name": "Nguyen Van A",
  "email": "patient.a@example.com",
  "password": "securePassword123",
  "phone": "0901234567",
  "role": "PATIENT"
}
```

**Trường hợp 2: Đăng ký là Người chăm sóc (Caretaker)**

```json
{
  "full_name": "Tran Thi B",
  "email": "caretaker.b@example.com",
  "password": "securePassword123",
  "phone": "0909876543",
  "role": "CARETAKER",
  "patient_full_name": "Nguyen Van A",
  "patient_email": "patient.a@example.com",
  "patient_phone": "0901234567"
}
```

#### Response

**Success (200 OK)**

**Trường hợp Role = PATIENT**

```json
{
  "code": "000",
  "message": "Thành công",
  "data": {
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "Nguyen Van A",
    "email": "patient.a@example.com",
    "phone": "0901234567",
    "is_active": true,
    "role": "PATIENT",
    "patient": null
  }
}
```

**Trường hợp Role = CARETAKER**

```json
{
  "code": "000",
  "message": "Thành công",
  "data": {
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "Tran Thi B",
    "email": "caretaker.b@example.com",
    "phone": "0909876543",
    "is_active": true,
    "role": "CARETAKER",
    "patient": {
        "user_id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
        "full_name": "Nguyen Van A",
        "email": "patient.a@example.com",
        "phone": "0901234567"
    }
  }
}
```

**Error (400 Bad Request)**

*   Email đã tồn tại.
*   Thiếu thông tin patient khi đăng ký caretaker.

```json
{
  "code": "400",
  "message": "Patient email and full name are required for Caretaker registration"
}
```

## 3. Task Management (Quản lý nhiệm vụ)

### 3.1. Get Patient Tasks by Date (Xem nhiệm vụ của bệnh nhân theo ngày)

API dành riêng cho **Bệnh nhân (PATIENT)** để xem danh sách các nhiệm vụ của chính mình trong một ngày cụ thể.

*   **URL**: `/api/tasks/patient/by-date`
*   **Method**: `GET`
*   **Headers**:
    *   `Authorization`: `Bearer <access_token>` (Token của Patient)

#### Query Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `task_date` | date | **Yes** | Ngày cần xem nhiệm vụ. Định dạng: `YYYY-MM-DD`. |

#### Response

Trả về danh sách các nhiệm vụ của bệnh nhân trong ngày.

```json
{
  "data": [
    {
      "title": "Uống thuốc sáng",
      "description": "Uống 1 viên Panadol sau ăn",
      "task_date": "2023-10-27",
      "task_time": "08:00:00",
      "task_type": "MEDICATION",
      "status": "PENDING",
      "owner_type": "PATIENT",
      "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "care_plan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "medication_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "nutrition_id": null,
      "exercise_id": null,
      "linked_task_id": null
    },
    {
      "title": "Tập vật lý trị liệu",
      "description": "Bài tập co duỗi chân",
      "task_date": "2023-10-27",
      "task_time": "10:00:00",
      "task_type": "EXERCISE",
      "status": "COMPLETED",
      "owner_type": "PATIENT",
      "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
      "care_plan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "medication_id": null,
      "nutrition_id": null,
      "exercise_id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
      "linked_task_id": null
    }
  ]
}
```

#### Error Responses

*   **400 Bad Request**: Lỗi định dạng ngày hoặc lỗi hệ thống.
*   **401 Unauthorized**: Chưa đăng nhập hoặc token hết hạn.
*   **403 Forbidden**: Người dùng không phải là Patient.

## 4. Patient Profile Management (Quản lý hồ sơ bệnh nhân)

### 4.1. Create Patient General Profile (Tạo hồ sơ tổng quát)

API cho Caretaker tạo hồ sơ tổng quát cho bệnh nhân của mình.

*   **URL**: `/api/patient-profile/general`
*   **Method**: `POST`
*   **Headers**:
    *   `Authorization`: `Bearer <access_token>` (Token của Caretaker)

#### Request Body

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `gender` | string | No | Giới tính: `MALE`, `FEMALE`, `OTHER` |
| `living_arrangement` | string | No | Môi trường sống |
| `bmi_score` | number | No | Chỉ số BMI |
| `map_score` | number | No | Chỉ số MAP (Mean Arterial Pressure) |
| `rhr_score` | number | No | Chỉ số RHR (Resting Heart Rate) |
| `adl_score` | number | No | Chỉ số ADL (Activities of Daily Living) |
| `iadl_score` | number | No | Chỉ số IADL (Instrumental Activities of Daily Living) |
| `blood_glucose_level` | number | No | Mức đường huyết |
| `disease_type` | string | **Yes** | Loại bệnh: `PHYSICAL_THERAPY`, `MENTAL_DECLINE`, `LONELINESS` |
| `condition_note` | string | No | Ghi chú về tình trạng |

#### Response

```json
{
  "code": "000",
  "message": "Thành công",
  "data": {
    "profile_id": "uuid",
    "patient_id": "uuid",
    "gender": "MALE",
    "living_arrangement": "string",
    "bmi_score": 25.5,
    "map_score": 90.0,
    "rhr_score": 70.0,
    "adl_score": 8.0,
    "iadl_score": 6.0,
    "blood_glucose_level": 100.0,
    "disease_type": "PHYSICAL_THERAPY",
    "condition_note": "string",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T10:00:00Z"
  }
}
```

### 4.2. Get Patient General Profile (Xem hồ sơ tổng quát)

API để xem hồ sơ tổng quát của bệnh nhân.

*   **URL**: `/api/patient-profile/general`
*   **Method**: `GET`
*   **Headers**:
    *   `Authorization`: `Bearer <access_token>`

#### Response

Tương tự như trên.

### 4.3. Update Patient General Profile (Cập nhật hồ sơ tổng quát)

API để cập nhật hồ sơ tổng quát của bệnh nhân.

*   **URL**: `/api/patient-profile/general`
*   **Method**: `PUT`
*   **Headers**:
    *   `Authorization`: `Bearer <access_token>`

#### Request Body

Tương tự Create, nhưng tất cả fields đều optional (partial update).

#### Response

Tương tự như Create.

### 4.4. Delete Patient General Profile (Xóa hồ sơ tổng quát)

API để xóa hồ sơ tổng quát của bệnh nhân.

*   **URL**: `/api/patient-profile/general`
*   **Method**: `DELETE`
*   **Headers**:
    *   `Authorization`: `Bearer <access_token>`

#### Response

```json
{
  "code": "000",
  "message": "Profile deleted successfully",
  "data": null
}
```

#### Error Responses

*   **400 Bad Request**: Hồ sơ không tồn tại hoặc lỗi hệ thống.
*   **401 Unauthorized**: Chưa đăng nhập hoặc token hết hạn.
*   **403 Forbidden**: Không có quyền truy cập hồ sơ này.

### 4.5. Delete Patient Physical Therapy Profile (Xóa hồ sơ vật lý trị liệu)

API để xóa hồ sơ vật lý trị liệu của bệnh nhân.

*   **URL**: `/api/patient-profile/physical-therapy`
*   **Method**: `DELETE`
*   **Headers**:
    *   `Authorization`: `Bearer <access_token>`

#### Response

```json
{
  "code": "000",
  "message": "Physical therapy profile deleted successfully",
  "data": null
}
```

#### Error Responses

*   **400 Bad Request**: Hồ sơ không tồn tại hoặc lỗi hệ thống.
*   **401 Unauthorized**: Chưa đăng nhập hoặc token hết hạn.
*   **403 Forbidden**: Không có quyền truy cập hồ sơ này.
