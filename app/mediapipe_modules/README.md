# MEMOTION - MediaPipe Integration

## Mô tả dự án

MEMOTION là một ứng dụng tích hợp hoàn chỉnh sử dụng MediaPipe để phân tích và đánh giá chuyển động cơ thể. Ứng dụng bao gồm 4 giai đoạn chính:

1. **PHASE 1: Pose Detection** - Nhận diện tư thế, vẽ skeleton
2. **PHASE 2: Safe-Max Calibration** - Đo giới hạn vận động an toàn
3. **PHASE 3: Motion Sync** - Đồng bộ với video mẫu
4. **PHASE 4: Scoring & Analysis** - Chấm điểm và phân tích chất lượng tập luyện

## Tính năng chính

- **Nhận diện tư thế thời gian thực** sử dụng MediaPipe Pose
- **Calibration an toàn** để đo giới hạn vận động của từng khớp
- **Đồng bộ chuyển động** với video mẫu sử dụng DTW (Dynamic Time Warping)
- **Chấm điểm đa chiều** bao gồm:
  - ROM Score: Mức độ đạt góc mục tiêu
  - Stability Score: Độ ổn định trong pha HOLD
  - Flow Score: Độ mượt mà của chuyển động
  - Symmetry Score: Cân bằng trái-phải
- **Phân tích mệt mỏi** dựa trên jerk (đạo hàm bậc 3 của vị trí)
- **Giao diện người dùng** với text tiếng Việt và visualization rõ ràng
- **Logging session** để theo dõi tiến trình

## Yêu cầu hệ thống

- Python 3.8+
- OpenCV
- MediaPipe
- NumPy
- PIL (Pillow)
- Các dependencies khác

## Cài đặt

1. Clone repository và chuyển vào thư mục mediapipe:
   ```bash
   cd mediapipe
   ```

2. Cài đặt dependencies:
   ```bash
   pip install opencv-python mediapipe numpy pillow
   ```

3. Đảm bảo có camera/webcam để sử dụng chế độ webcam

## Cách sử dụng

### Chạy ứng dụng chính

```bash
# Chế độ webcam với video tham khảo
python main_final.py --source webcam --ref-video exercise.mp4

# Chế độ test
python main_final.py --mode test

# Hoặc sử dụng main_v2.py (phiên bản mở rộng)
python main_v2.py --source webcam --ref-video exercise.mp4
```

### Điều khiển

- **SPACE**: Pause/Resume hoặc Bắt đầu calibration
- **R**: Restart
- **Q**: Quit
- **1-6**: Chọn khớp để đo (Phase 2)
  - 1: Vai trái
  - 2: Vai phải
  - 3: Khủy tay trái
  - 4: Khủy tay phải
  - 5: Đầu gối trái
  - 6: Đầu gối phải
- **ENTER**: Xác nhận/Chuyển phase tiếp theo
- **ESC**: Thoát

## Cấu trúc thư mục

```
mediapipe/
├── main_final.py          # Script chính (phiên bản final)
├── main_v2.py            # Script chính (phiên bản mở rộng)
├── modules/
│   └── scoring.py        # Module chấm điểm và phân tích
├── utils/
│   ├── __init__.py
│   └── visualization.py  # Các hàm visualization và UI
├── data/
│   └── logs/             # Logs của các session
├── test_logs/            # Logs test
└── scripts/              # Scripts hỗ trợ
```

## Modules chính

### scoring.py
- Chấm điểm đa chiều cho từng rep
- Phân tích mệt mỏi dựa trên jerk
- Tính toán symmetry và stability

### visualization.py
- Vẽ skeleton và keypoints
- Hiển thị text tiếng Việt
- Vẽ UI panels, progress bars

## Định dạng dữ liệu

- **Session logs**: JSON files trong `data/logs/YYYYMMDD/`
- **Test logs**: JSON files trong `test_logs/YYYYMMDD/`
- **Joint types**: LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_ELBOW, RIGHT_ELBOW, LEFT_KNEE, RIGHT_KNEE

## Phát triển

### Thêm bài tập mới
1. Tạo function tạo bài tập trong `core/exercises.py`
2. Thêm vào MotionSyncController
3. Cập nhật UI trong main scripts

### Tùy chỉnh scoring
Sửa đổi các trọng số và công thức trong `modules/scoring.py`

### Thêm ngôn ngữ
Cập nhật dictionaries trong `utils/visualization.py`

## Troubleshooting

### Lỗi camera
- Đảm bảo camera không bị chiếm bởi ứng dụng khác
- Kiểm tra quyền truy cập camera

### Lỗi dependencies
```bash
pip install opencv-python mediapipe numpy pillow
```

### Performance issues
- Giảm độ phân giải camera trong DetectorConfig
- Tắt một số tính năng visualization

## Tác giả

MEMOTION Team

## Phiên bản

2.0.0

## License

[Thêm license nếu có]