# Hướng dẫn Cấu trúc Dự án và Quy chuẩn Code (Clean Architecture & SOLID)

Tài liệu này mô tả cấu trúc source code, quy chuẩn lập trình và cách áp dụng các nguyên lý SOLID vào dự án Memotion. Mục tiêu là đảm bảo code dễ bảo trì, dễ mở rộng và tuân thủ các tiêu chuẩn kỹ thuật cao.

## 1. Cấu trúc Thư mục

Cấu trúc dự án được tổ chức theo mô hình phân lớp (Layered Architecture), tách biệt rõ ràng giữa các thành phần:

```
app/
├── api/            # Presentation Layer: Định nghĩa các endpoints, xử lý HTTP request/response.
├── core/           # Core: Cấu hình hệ thống, bảo mật, logging, constants.
├── db/             # Database: Cấu hình kết nối DB, session management.
├── helpers/        # Utilities: Các hàm tiện ích, exception handling, paging.
├── models/         # Entities: Định nghĩa các model tương ứng với bảng trong Database (SQLAlchemy).
├── repository/     # Data Access Layer: Thực hiện các truy vấn Database trực tiếp.
├── schemas/        # DTOs: Pydantic models dùng để validate dữ liệu đầu vào/ra (Request/Response).
├── services/       # Business Logic Layer: Xử lý nghiệp vụ chính, gọi xuống Repository.
└── main.py         # Entry point của ứng dụng.
```

## 2. Trách nhiệm của từng Layer (Separation of Concerns)

### 2.1. API Layer (`app/api`)
- **Trách nhiệm**:
  - Định nghĩa các đường dẫn (URL endpoints).
  - Nhận request từ client.
  - Validate dữ liệu sơ bộ (thông qua `Depends` hoặc Pydantic schemas).
  - Gọi xuống **Service Layer** để xử lý nghiệp vụ.
  - Trả về response chuẩn (HTTP Status code, JSON format).
- **Nguyên tắc**:
  - **KHÔNG** viết logic nghiệp vụ phức tạp tại đây.
  - **KHÔNG** gọi trực tiếp Database (`db.session.query`) tại đây.

### 2.2. Service Layer (`app/services`)
- **Trách nhiệm**:
  - Chứa toàn bộ logic nghiệp vụ (Business Logic) của hệ thống.
  - Xử lý các quy tắc nghiệp vụ, tính toán, validate logic.
  - Gọi **Repository Layer** để lấy hoặc lưu dữ liệu.
  - Xử lý transaction (commit/rollback) nếu cần thiết (hoặc để Repository xử lý tùy strategy).
- **Nguyên tắc**:
  - Tách biệt hoàn toàn với HTTP (không nên return trực tiếp `HTTPException` nếu có thể, hãy raise Custom Exception để API layer bắt).
  - Chỉ làm việc với Domain Models hoặc DTOs.

### 2.3. Repository Layer (`app/repository`)
- **Trách nhiệm**:
  - Trực tiếp tương tác với Database (CRUD: Create, Read, Update, Delete).
  - Xây dựng các câu query phức tạp.
  - Ẩn chi tiết về ORM (SQLAlchemy) khỏi Service layer.
- **Nguyên tắc**:
  - Chỉ thực hiện query, không chứa logic nghiệp vụ.
  - Cung cấp các method rõ ràng: `get_by_id`, `create`, `update`, `delete`, `find_by_email`, v.v.

### 2.4. Schemas (`app/schemas`)
- **Trách nhiệm**:
  - Định nghĩa cấu trúc dữ liệu giao tiếp (Data Transfer Objects - DTO).
  - Validate kiểu dữ liệu, độ dài, format (email, phone...).
  - Tách biệt model database (`models`) và dữ liệu trả về cho client.

### 2.5. Models (`app/models`)
- **Trách nhiệm**:
  - Định nghĩa cấu trúc bảng trong Database.
  - Định nghĩa các quan hệ (Relationship) giữa các bảng.

## 3. Áp dụng SOLID

### 3.1. Single Responsibility Principle (SRP) - Nguyên lý đơn nhiệm
Mỗi class/module chỉ nên có một lý do để thay đổi.
- **Ví dụ**:
  - `UserAPI` chỉ lo việc nhận request/trả response user.
  - `UserService` chỉ lo logic nghiệp vụ user (đăng ký, đăng nhập, đổi pass).
  - `UserRepository` chỉ lo query bảng User.
  - Không trộn lẫn việc gửi email vào trong `UserRepository`.

### 3.2. Open/Closed Principle (OCP) - Nguyên lý đóng/mở
Class nên mở rộng được nhưng đóng với việc sửa đổi.
- **Áp dụng**: Sử dụng `BaseRepository` hoặc `BaseService`. Khi cần thêm chức năng cho một entity mới, ta kế thừa và mở rộng thay vì sửa code cũ của Base.

### 3.3. Liskov Substitution Principle (LSP) - Nguyên lý thay thế Liskov
Các class con phải có thể thay thế class cha mà không làm hỏng chương trình.
- **Áp dụng**: Nếu có `BaseRepository` định nghĩa hàm `get(id)`, thì `UserRepository` kế thừa từ đó cũng phải đảm bảo hàm `get(id)` hoạt động đúng ngữ nghĩa, không được throw exception lạ hoặc đổi kiểu trả về đột ngột.

### 3.4. Interface Segregation Principle (ISP) - Nguyên lý phân tách interface
Thay vì dùng 1 interface lớn, hãy tách thành nhiều interface nhỏ cụ thể.
- **Áp dụng**: Trong Python (dynamic typing), điều này thường áp dụng qua việc thiết kế các Service nhỏ gọn, không nhồi nhét tất cả logic vào một `SuperService`.

### 3.5. Dependency Inversion Principle (DIP) - Nguyên lý đảo ngược sự phụ thuộc
Module cấp cao không nên phụ thuộc module cấp thấp. Cả hai nên phụ thuộc vào abstraction.
- **Áp dụng**:
  - Service không nên khởi tạo trực tiếp Repository bên trong nó (hard dependency).
  - Nên sử dụng **Dependency Injection (DI)**. Trong FastAPI, ta dùng `Depends` để inject Service vào API, và inject Repository vào Service.

## 4. Ví dụ Triển khai (Code Snippet)

Dưới đây là ví dụ minh họa cách refactor code hiện tại để tuân thủ cấu trúc trên.

### 4.1. Repository (`app/repository/repo_user.py`)

```python
from sqlalchemy.orm import Session
from app.models.model_user import User
from app.schemas.sche_user import UserCreateRequest

class UserRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user_data: UserCreateRequest) -> User:
        user = User(**user_data.dict())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
```

### 4.2. Service (`app/services/srv_user.py`)

```python
from fastapi import Depends
from app.repository.repo_user import UserRepository
from app.schemas.sche_user import UserCreateRequest
from app.core.security import get_password_hash

class UserService:
    def __init__(self, user_repo: UserRepository = Depends()):
        self.user_repo = user_repo

    def register_user(self, user_data: UserCreateRequest):
        # Business Logic: Check if user exists
        if self.user_repo.get_by_email(user_data.email):
            raise Exception("Email already exists")
        
        # Business Logic: Hash password
        user_data.password = get_password_hash(user_data.password)
        
        # Call Repository to save
        return self.user_repo.create(user_data)
```

### 4.3. API (`app/api/api_user.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.srv_user import UserService
from app.schemas.sche_user import UserCreateRequest, UserItemResponse

router = APIRouter()

@router.post("/register", response_model=UserItemResponse)
def register(
    user_data: UserCreateRequest, 
    service: UserService = Depends() # Dependency Injection
):
    try:
        return service.register_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 5. Quy trình phát triển (Workflow)

1.  **Định nghĩa Model**: Tạo file trong `app/models/`.
2.  **Định nghĩa Schema**: Tạo Request/Response schema trong `app/schemas/`.
3.  **Tạo Repository**: Viết query DB trong `app/repository/`.
4.  **Viết Service**: Viết logic nghiệp vụ trong `app/services/`, gọi Repository.
5.  **Viết API**: Tạo endpoint trong `app/api/`, gọi Service.
6.  **Đăng ký Router**: Thêm router vào `app/api/api_router.py`.

## 6. Quy chuẩn Đặt tên và Clean Code

### 6.1. Naming Conventions (Theo chuẩn PEP 8)

Việc đặt tên nhất quán giúp code dễ đọc và dễ hiểu hơn.

*   **Biến (Variables) & Hàm (Functions)**: Sử dụng `snake_case`.
    *   Đúng: `user_name`, `get_user_by_id()`, `calculate_total_price()`
    *   Sai: `UserName`, `getUserById`, `CalculateTotalPrice`
*   **Lớp (Classes)**: Sử dụng `PascalCase` (CapitalizedWords).
    *   Đúng: `UserService`, `UserRepository`, `UserProfile`
    *   Sai: `userService`, `user_repository`
*   **Hằng số (Constants)**: Sử dụng `UPPER_CASE` với dấu gạch dưới.
    *   Đúng: `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE`
    *   Sai: `maxRetryCount`, `DefaultPageSize`
*   **Module/File**: Sử dụng `snake_case`, ngắn gọn.
    *   Đúng: `srv_user.py`, `api_auth.py`
    *   Sai: `SrvUser.py`, `APIAuth.py`
*   **Private Members**: Bắt đầu bằng dấu gạch dưới `_`.
    *   Ví dụ: `_db_session`, `_validate_input()`

### 6.2. Clean Code Principles

*   **Tên biến có ý nghĩa (Meaningful Names)**:
    *   Tránh đặt tên tắt vô nghĩa như `x`, `y`, `temp`, `data`.
    *   Thay vào đó dùng: `user_age`, `file_path`, `temporary_file`, `user_data`.
*   **Hàm nhỏ và làm một việc (Small Functions & Do One Thing)**:
    *   Một hàm không nên quá dài (lý tưởng < 20 dòng).
    *   Nếu hàm làm nhiều việc (vừa validate, vừa query DB, vừa gửi mail), hãy tách thành các hàm nhỏ hơn.
*   **Tránh Magic Numbers/Strings**:
    *   Không dùng số cứng trong code (ví dụ: `if status == 1`).
    *   Hãy định nghĩa Enum hoặc Constant: `if status == UserStatus.ACTIVE`.
*   **Comment đúng chỗ**:
    *   Code nên tự giải thích (Self-documenting code).
    *   Chỉ comment để giải thích "Tại sao" (Why), không giải thích "Cái gì" (What) nếu code đã rõ ràng.

### 6.3. RESTful API Design Guidelines

*   **Sử dụng danh từ số nhiều cho Resource**:
    *   `GET /users`: Lấy danh sách user.
    *   `GET /users/{id}`: Lấy chi tiết user.
    *   `POST /users`: Tạo user mới.
    *   `PUT /users/{id}`: Cập nhật toàn bộ user.
    *   `PATCH /users/{id}`: Cập nhật một phần user.
    *   `DELETE /users/{id}`: Xóa user.
*   **Không dùng động từ trong URL**:
    *   Sai: `/getUsers`, `/createUser`, `/updateUser`.
    *   Đúng: Dùng HTTP Methods (GET, POST, PUT, DELETE) để định nghĩa hành động.
*   **Sử dụng HTTP Status Codes chuẩn**:
    *   `200 OK`: Thành công.
    *   `201 Created`: Tạo mới thành công.
    *   `400 Bad Request`: Lỗi dữ liệu đầu vào.
    *   `401 Unauthorized`: Chưa đăng nhập.
    *   `403 Forbidden`: Không có quyền truy cập.
    *   `404 Not Found`: Không tìm thấy tài nguyên.
    *   `500 Internal Server Error`: Lỗi hệ thống.
*   **Filtering, Sorting, Paging**:
    *   Sử dụng query parameters: `GET /users?page=1&limit=10&sort=-created_at&role=admin`.

---
*Tài liệu này dùng để định hướng phát triển cho team Memotion.*
