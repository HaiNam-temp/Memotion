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
