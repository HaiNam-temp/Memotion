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

### 6.4. Standard Response Format

Tất cả các API **BẮT BUỘC** phải trả về response theo cấu trúc chuẩn được định nghĩa trong `app.schemas.sche_base`.

*   **Cấu trúc chuẩn**:
    ```json
    {
        "success": true,
        "message": "Thành công",
        "data": { ... }
    }
    ```
*   **Thành công**: Sử dụng `DataResponse[T].success_response(data=...)`.
*   **Lỗi**:
    *   Sử dụng `CustomException(http_code=..., code=..., message=...)` để throw lỗi.
    *   Exception handler sẽ tự động bắt và trả về format chuẩn:
        ```json
        {
            "success": false,
            "message": "Chi tiết lỗi",
            "data": null
        }
        ```
*   **Tuyệt đối KHÔNG** return trực tiếp dictionary hoặc `HTTPException` của FastAPI (trừ khi đã được wrap bởi handler).

### 6.5. Swagger Documentation Guidelines

Tất cả các API endpoint **BẮT BUỘC** phải có docstring chi tiết để tự động tạo tài liệu Swagger/OpenAPI đầy đủ và dễ hiểu.

*   **Cấu trúc Docstring**:
    - **Dòng đầu**: Mô tả ngắn gọn chức năng của API (1-2 câu).
    - **Authorization**: Xác định role hoặc quyền cần thiết để truy cập API.
    - **Process**: Liệt kê các bước xử lý chính theo thứ tự.
    - **Response**: Mô tả nội dung trả về.

*   **Ví dụ**:
    ```python
    @router.post('/generate', response_model=DataResponse[CarePlanGenerationResponse])
    def generate_care_plan(...):
        """
        Generate AI-powered care plan for patient.
        
        This API creates a personalized care plan using Gemini AI based on patient's profile, 
        therapy history, and current health status. The plan includes daily tasks, medication 
        reminders, exercise routines, and nutritional recommendations tailored to the patient's needs.
        
        **Authorization**: CARETAKER role required.
        
        **Process**:
        1. Validates caretaker has assigned patient
        2. Loads patient profile and therapy details
        3. Calls Gemini AI to generate personalized care plan
        4. Creates care_plan and task records in database
        
        **Response**: Care plan summary with task count and recommendations.
        """
    ```

*   **Quy tắc viết**:
    - Sử dụng **Markdown** trong docstring để format (bold, italic, lists).
    - Mô tả **Process** theo thứ tự logic, sử dụng số thứ tự.
    - **Authorization** phải rõ ràng (role, permission cụ thể).
    - **Response** tóm tắt nội dung chính, không cần chi tiết schema (đã có response_model).
    - Docstring phải bằng tiếng Anh để tương thích với Swagger.

## 7. Logging Guidelines

Việc ghi log là bắt buộc để theo dõi hoạt động của hệ thống và debug lỗi.

*   **Import Logger**:
    ```python
    import logging
    logger = logging.getLogger(__name__)
    ```
*   **Log Levels**:
    *   `INFO`: Ghi lại các sự kiện quan trọng (Request nhận được, xử lý thành công).
    *   `ERROR`: Ghi lại lỗi xảy ra (Exception).
    *   `DEBUG`: Ghi lại thông tin chi tiết để debug (chỉ bật khi cần thiết).
*   **Format Log**:
    *   **Request**: `logger.info(f"{function_name} request: user_id={user_id}, data={data}")`
    *   **Success**: `logger.info(f"{function_name} success: result_id={id}")`
    *   **Error**: `logger.error(f"{function_name} error: {str(e)}", exc_info=True)`
*   **Clean Log**:
    *   Log ngắn gọn, đủ thông tin.
    *   Không log thông tin nhạy cảm (password, token).
    *   Luôn dùng `exc_info=True` khi log error để in ra stack trace.

## 8. Strict Rules (Quy Tắc Nghiêm Ngặt)

Để đảm bảo chất lượng code và tính nhất quán, **Memotion project áp dụng các quy tắc nghiêm ngặt sau**. Vi phạm sẽ bị từ chối trong code review.

### 8.1. Type Hints (Bắt Buộc)

*   **Tất cả functions/methods** phải có type hints đầy đủ:
    ```python
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        pass
    ```
*   **Không dùng `Any`** trừ khi thực sự cần thiết (và phải giải thích lý do).
*   **Sử dụng Union types** thay vì Optional khi có nhiều kiểu:
    ```python
    def process_data(self, data: Union[dict, list]) -> bool:
        pass
    ```

### 8.2. Docstring (Bắt Buộc)

*   **Tất cả public methods** phải có docstring theo format Google/Numpy.
*   **Tất cả classes** phải có docstring mô tả trách nhiệm.
*   **Docstring tối thiểu** bao gồm: Mô tả ngắn, Args, Returns, Raises.

### 8.3. Exception Handling (Bắt Buộc)

*   **Không bao giờ catch generic Exception**:
    ```python
    # SAI
    try:
        do_something()
    except Exception as e:
        pass
    
    # ĐÚNG
    try:
        do_something()
    except ValueError as e:
        handle_value_error()
    except ConnectionError as e:
        handle_connection_error()
    ```
*   **Luôn raise CustomException** thay vì built-in exceptions.
*   **Log tất cả exceptions** với `exc_info=True`.

### 8.4. Dependency Injection (Bắt Buộc)

*   **Không khởi tạo dependencies trực tiếp** trong class:
    ```python
    # SAI
    class UserService:
        def __init__(self):
            self.repo = UserRepository()  # Hard dependency
    
    # ĐÚNG
    class UserService:
        def __init__(self, repo: UserRepository = Depends()):
            self.repo = repo  # Injected
    ```

### 8.5. Database Transactions (Bắt Buộc)

*   **Tất cả DB operations** phải trong transaction context.
*   **Service layer** chịu trách nhiệm commit/rollback.
*   **Không commit trong Repository layer**.

### 8.6. Testing (Bắt Buộc)

*   **Tất cả business logic** phải có unit tests.
*   **Test coverage** tối thiểu 80%.
*   **API endpoints** phải có integration tests.
*   **Sử dụng pytest** framework.

### 8.7. Code Review Requirements

*   **Pull Request** phải có:
    - Description chi tiết về thay đổi
    - Test cases pass
    - Code review từ ít nhất 1 reviewer
    - Không có linting errors
*   **Blocking Issues**:
    - Syntax errors
    - Import errors
    - Missing type hints
    - Missing docstrings
    - Missing tests
    - Security vulnerabilities

### 8.8. Security Rules

*   **Không log sensitive data**: password, tokens, PII.
*   **Validate tất cả inputs** từ user.
*   **Sử dụng parameterized queries** (SQLAlchemy đã handle).
*   **Rate limiting** cho public APIs.
*   **Input sanitization** cho text fields.

### 8.9. Performance Rules

*   **Không query N+1**: Sử dụng joins hoặc batch loading.
*   **Pagination bắt buộc** cho list APIs.
*   **Cache** cho dữ liệu thường xuyên truy cập.
*   **Async** cho I/O operations (nếu cần).

### 8.10. File Structure Rules

*   **Một class per file** (trừ utility classes).
*   **Max 300 lines per file**.
*   **Max 50 lines per function**.
*   **Alphabetical import ordering**.

### 8.11. Naming Conventions (Strict)

*   **Constants**: `UPPER_SNAKE_CASE`
*   **Variables/Functions**: `snake_case`
*   **Classes**: `PascalCase`
*   **Private members**: `_leading_underscore`
*   **Files**: `snake_case.py`

### 8.12. Git Workflow

*   **Feature branches**: `feature/feature-name`
*   **Bug fixes**: `fix/bug-description`
*   **Hot fixes**: `hotfix/critical-issue`
*   **Squash commits** trước khi merge.
*   **Rebase** thay vì merge conflicts.

### 8.13. Monitoring & Alerting

*   **Application metrics** phải được expose (response time, error rate).
*   **Health checks** cho tất cả dependencies.
*   **Alert** cho critical errors.
*   **Log aggregation** và monitoring.

### 8.14. Documentation

*   **README.md** phải up-to-date.
*   **API documentation** tự động từ docstrings.
*   **Architecture decisions** phải được document.
*   **Deployment guide** chi tiết.

## 9. AI & MediaPipe Integration Rules

### 9.1. AI Service Architecture

**Nguyên tắc thiết kế AI Services:**
- **Service Layer Centralization**: Tất cả logic AI processing phải được tập trung trong Service Layer (`app/services/srv_pose_detection.py`).
- **MediaPipe Integration**: Service phải sử dụng trực tiếp các modules từ `mediapipe_integration` thay vì implement logic riêng.
- **Phase-Based Processing**: Tuân thủ strict 3-phase logic (Detection → Measuring → Scoring) với transition rules rõ ràng.

**Cấm tuyệt đối:**
- ❌ **KHÔNG** viết logic AI processing trong API Layer.
- ❌ **KHÔNG** duplicate MediaPipe functions trong Service.
- ❌ **KHÔNG** bypass Service Layer để gọi MediaPipe trực tiếp từ API.

### 9.2. MediaPipe Module Usage

**Required Components:**
```python
# VisionDetector - Phase 1 (Detection)
from ..mediapipe_integration.core import VisionDetector, DetectorConfig

# Kinematics - Phase 2 (Measuring)
from ..mediapipe_integration.core import calculate_joint_angle, PoseLandmarkIndex

# HealthScorer - Phase 3 (Scoring)
from ..mediapipe_integration.modules import HealthScorer

# MotionSyncController - Reference video sync
from ..mediapipe_integration.core import MotionSyncController

# VideoEngine - Reference video processing
from ..mediapipe_integration.modules import VideoEngine
```

**Phase Implementation Rules:**
- **Phase 1 (Detection)**: Sử dụng `VisionDetector.process_frame()` để detect person và tính stability.
- **Phase 2 (Measuring)**: Sử dụng `calculate_joint_angle()` để tính angles, thu thập motion data.
- **Phase 3 (Scoring)**: Sử dụng `HealthScorer` methods để tính ROM, stability, flow, symmetry scores.

### 9.3. Service Method Structure

```python
class PoseDetectionService:
    async def start_pose_session(self, ...) -> Dict[str, Any]:
        """Initialize MediaPipe components for session"""

    async def process_frame_stream(self, session_id, frame_data, phase) -> Dict[str, Any]:
        """Route to phase-specific processing"""

    async def _process_detection_frame(self, session, frame_data) -> Dict[str, Any]:
        """Phase 1: Use VisionDetector"""

    async def _process_measuring_frame(self, session, frame_data) -> Dict[str, Any]:
        """Phase 2: Use kinematics functions"""

    async def _process_scoring_frame(self, session, frame_data) -> Dict[str, Any]:
        """Phase 3: Use HealthScorer + MotionSyncController"""
```

### 9.4. API Layer Responsibilities

**API Layer chỉ được:**
- ✅ Nhận WebSocket frame data
- ✅ Validate session existence
- ✅ Gọi `pose_detection_service.process_frame_stream()`
- ✅ Forward service response về client
- ✅ Handle connection management

**API Layer KHÔNG được:**
- ❌ Process frame data
- ❌ Calculate angles/scores
- ❌ Access MediaPipe modules
- ❌ Implement phase logic

### 9.5. Error Handling & Logging

**Service Layer:**
- Log tất cả phase transitions
- Log frame processing metrics
- Handle MediaPipe exceptions gracefully
- Return structured error responses

**API Layer:**
- Log WebSocket events
- Forward service errors to client
- Maintain connection stability

### 9.6. Testing Requirements

**Unit Tests:**
- Test each MediaPipe function integration
- Mock frame data for phase testing
- Test phase transition logic

**Integration Tests:**
- End-to-end WebSocket flow
- Service-API communication
- MediaPipe pipeline validation

### 9.7. Performance Guidelines

- **Frame Processing**: < 100ms per frame
- **Memory Management**: Cleanup session components
- **Concurrent Sessions**: Support multiple users
- **Resource Limits**: Monitor MediaPipe resource usage

---

*Tài liệu này dùng để định hướng phát triển cho team Memotion.*

