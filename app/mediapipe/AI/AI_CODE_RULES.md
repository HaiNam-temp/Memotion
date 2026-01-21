# AI Code Logic Rules - Follow Project Structure

## Tổng quan
Tài liệu này định nghĩa các quy tắc lập trình cho layer AI trong dự án Memotion, đảm bảo tuân thủ cấu trúc dự án Clean Architecture và nguyên lý SOLID.

## 1. Vị trí và Cấu trúc Layer AI

### 1.1. Vị trí Packet AI
- **ĐÚNG**: Packet AI phải nằm trong `app/mediapipe/AI/`
- **SAI**: Không đặt AI trực tiếp trong `app/` hoặc ngoài `mediapipe/`
- **Lý do**: AI là phần mở rộng của mediapipe, phải nằm trong package mediapipe

### 1.2. Cấu trúc Thư mục AI
```
app/mediapipe/AI/
├── service/          # Service layer - Interface cho AI algorithms
├── controller/       # Controller layer - Điều khiển luồng xử lý
├── data/            # Data processing - Xử lý dữ liệu đầu vào/ra
└── README.md        # Tài liệu
```

## 2. Nguyên tắc Thiết kế AI Layer

### 2.1. Không Tạo Logic Xử Lý Mới
- **QUY TẮC**: Các hàm trong AI **KHÔNG** được chứa logic xử lý trực tiếp
- **THỰC HIỆN**: Chỉ gọi xuống các hàm thuật toán ở `mediapipe/core/` và `mediapipe/modules/`
- **VÍ DỤ SAI**:
  ```python
  # SAI: Tạo logic mới trong AI
  def calculate_angle(points):  # Không được tạo hàm tính toán mới
      # Logic tính toán trực tiếp
      pass
  ```
- **VÍ DỤ ĐÚNG**:
  ```python
  # ĐÚNG: Chỉ gọi hàm từ core
  from ..core.kinematics import calculate_angle
  
  def get_joint_angle(landmarks):
      return calculate_angle(landmarks)
  ```

### 2.2. Tái Sử Dụng Hoàn Toàn Thuật Toán Mediapipe
- **QUY TẮC**: Không sửa đổi, override, hoặc tạo version mới của thuật toán trong mediapipe
- **THỰC HIỆN**: Import và sử dụng trực tiếp từ `mediapipe/core/` và `mediapipe/modules/`
- **CẤM**: Thay đổi logic, tham số, hoặc kết quả của các thuật toán gốc

### 2.3. Không Sửa Đổi Logic Thuật Toán Mediapipe
- **QUY TẮC**: Các file trong `mediapipe/core/` và `mediapipe/modules/` **KHÔNG** được sửa đổi
- **THỰC HIỆN**: Nếu cần customize, tạo wrapper trong AI layer mà không thay đổi core
- **LÝ DO**: Bảo toàn tính toàn vẹn và tính chính xác của thuật toán AI

## 3. Áp dụng SOLID Principles

### 3.1. Single Responsibility Principle (SRP)
- Mỗi class trong AI chỉ có **một trách nhiệm duy nhất**
- **Service Layer**: Chỉ orchestrate các call đến core algorithms
- **Controller Layer**: Chỉ điều khiển luồng xử lý, không chứa business logic
- **Data Layer**: Chỉ xử lý format dữ liệu, không chứa tính toán

### 3.2. Open/Closed Principle (OCP)
- AI components phải **mở rộng được** nhưng **đóng với sửa đổi**
- Sử dụng inheritance và composition để mở rộng chức năng
- Không sửa đổi code hiện có khi thêm feature mới

### 3.3. Liskov Substitution Principle (LSP)
- Các subclass phải có thể thay thế parent class mà không làm hỏng chức năng
- Đảm bảo interface consistency khi implement các AI services

### 3.4. Interface Segregation Principle (ISP)
- Tạo interfaces nhỏ, specific thay vì một interface lớn
- Mỗi AI service chỉ implement các methods cần thiết

### 3.5. Dependency Inversion Principle (DIP)
- AI layer phụ thuộc vào abstractions (interfaces), không phải concrete implementations
- Inject dependencies từ core/modules qua constructor hoặc parameters

## 4. Quy tắc Import và Dependencies

### 4.1. Import Rules
- **ĐƯỢC PHÉP**: Import từ `mediapipe.core.*` và `mediapipe.modules.*`
- **ĐƯỢC PHÉP**: Import từ các package standard library
- **CẤM**: Import từ `app.services.*` hoặc các layer cao hơn
- **CẤM**: Circular imports giữa AI và services

### 4.2. Dependency Injection
- Sử dụng constructor injection cho các dependencies từ core
- Tránh hard-coded dependencies
- Sử dụng factories hoặc builders để tạo AI components

## 5. Quy tắc Testing và Validation

### 5.1. Unit Testing
- Test AI layer riêng biệt với core algorithms
- Mock dependencies từ core/modules
- Verify rằng AI chỉ gọi đúng functions từ core

### 5.2. Integration Testing
- Test tích hợp giữa AI và core algorithms
- Đảm bảo không có side effects khi thay đổi AI layer

## 6. Quy tắc Documentation

### 6.1. Code Comments
- Mỗi function phải có docstring mô tả purpose
- Comment tại sao gọi function từ core, không phải how
- Document các parameters và return values

### 6.2. README và Guides
- Cập nhật README.md khi thêm/chỉnh sửa AI components
- Document các dependencies và setup requirements

## 7. Quy trình Phát triển

### 7.1. Khi Thêm Feature Mới
1. Xác định thuật toán cần thiết trong core/modules
2. Tạo wrapper function trong AI/service/
3. Test integration với core
4. Update documentation

### 7.2. Khi Sửa Bug
1. Kiểm tra bug có trong core hay AI layer
2. Nếu trong core: Báo cáo và chờ fix từ core team
3. Nếu trong AI: Fix wrapper logic, không sửa core

### 7.3. Code Review Checklist
- [ ] Không tạo logic mới trong AI
- [ ] Chỉ gọi functions từ core/modules
- [ ] Tuân thủ SOLID principles
- [ ] Có unit tests
- [ ] Documentation đầy đủ
- [ ] Không có circular dependencies

## 8. Ví dụ Implementation

```python
# app/mediapipe/AI/service/pose_service.py
from ..core.detector import VisionDetector, DetectorConfig
from ..core.kinematics import calculate_joint_angle, JointType
from ..modules.scoring import HealthScorer

class PoseAIService:
    """
    AI Service for pose detection.
    
    This service orchestrates pose detection without implementing
    any core algorithms - just calls existing mediapipe functions.
    """
    
    def __init__(self, detector_config: DetectorConfig):
        # Inject dependencies from core
        self.detector = VisionDetector(detector_config)
        self.scorer = HealthScorer()
    
    def process_pose_frame(self, frame, timestamp):
        # Just call core functions - no new logic
        result = self.detector.process_frame(frame, timestamp)
        angles = calculate_joint_angle(result.pose_landmarks, JointType.LEFT_ELBOW)
        score = self.scorer.calculate_score(angles)
        return score
```

## 9. Monitoring và Maintenance

### 9.1. Version Control
- Track versions của core algorithms được sử dụng
- Document compatibility requirements

### 9.2. Performance Monitoring
- Monitor performance của AI calls đến core
- Alert khi có degradation trong core algorithms

---

**Lưu ý**: Tài liệu này phải được tuân thủ nghiêm ngặt để đảm bảo tính toàn vẹn của hệ thống AI và dễ bảo trì code.