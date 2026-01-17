# Pose Detection API Integration Guide

Hướng dẫn chi tiết cách tích hợp và sử dụng Pose Detection API từ phía Web/Mobile client.

## Tổng quan

Pose Detection API cho phép mobile app (Flutter) và web app thực hiện bài tập vật lý trị liệu với hướng dẫn real-time thông qua:

- **REST API**: Quản lý session
- **WebSocket**: Streaming feedback real-time
- **WebRTC**: Video streaming (framework ready)

## Luồng Kết nối Tuần tự

### Bước 1: Khởi tạo Session Pose Detection

**API tương ứng**: `POST /api/tasks/{task_id}/pose-session/start` (REST API)

**Mục đích của step này**:
- Tạo một phiên làm việc pose detection mới trên server
- Chuẩn bị các tài nguyên cần thiết cho việc xử lý video
- Thiết lập kết nối WebRTC để nhận video stream từ mobile

**Thông tin truyền đi (Input)**:
- `task_id`: ID của task vật lý trị liệu cần thực hiện
- `exercise_id`: ID của bài tập cụ thể (ví dụ: "arm_raise_001")
- `stream_type`: Loại streaming ("webrtc" hoặc "websocket")

**Thông tin nhận về (Output)**:
- `session_id`: ID duy nhất của phiên làm việc vừa tạo
- `webrtc_offer`: Thông tin kỹ thuật để thiết lập kết nối WebRTC
- `reference_video_url`: Link video mẫu để hiển thị hướng dẫn

**Logic xử lý trên server**:
1. Tạo session ID duy nhất
2. Chuẩn bị WebRTC peer connection
3. Tạo SDP offer để gửi cho client
4. Trả về thông tin kết nối cho mobile

### Bước 2: Khởi tạo Reference Video

**API tương ứng**: Không có API call, chỉ load URL từ bước 1

**Mục đích của step này**:
- Tải và hiển thị video hướng dẫn để người dùng có thể quan sát và bắt chước
- Tạo giao diện dual-screen: camera người dùng + video tham khảo

**Thông tin truyền đi**: Không có (chỉ nhận URL từ bước 1)

**Logic xử lý**:
- Mobile tải video từ URL được cung cấp
- Hiển thị video song song với camera preview
- Video chạy lặp lại để hướng dẫn liên tục

### Bước 3: Kết nối WebSocket

**API tương ứng**: `ws://api/tasks/{task_id}/pose-feedback` (WebSocket connection)

**Mục đích của step này**:
- Thiết lập kênh giao tiếp real-time riêng biệt với video stream
- Nhận feedback tức thời về tư thế của người dùng
- Gửi các lệnh điều khiển phiên làm việc

**Thông tin truyền đi**: Không có (chỉ thiết lập kết nối)

**Logic xử lý**:
- Mobile kết nối đến WebSocket endpoint
- Server xác nhận kết nối và chờ lệnh start session
- Chuẩn bị sẵn sàng nhận các message JSON

### Bước 4: Gửi Start Session Signal

**API tương ứng**: WebSocket message với type "start_session"

**Mục đích của step này**:
- Thông báo cho server bắt đầu xử lý pose detection
- Khởi động các engine xử lý video và phân tích tư thế
- Bắt đầu theo dõi tiến độ bài tập

**Thông tin truyền đi**:
- `type`: "start_session" (loại message)
- `task_id`: ID task để server xác định context
- `exercise_id`: ID bài tập để load reference pose

**Logic xử lý trên server**:
1. Load dữ liệu pose tham khảo cho bài tập
2. Khởi tạo MediaPipe detector
3. Chuẩn bị các thuật toán so sánh tư thế
4. Bắt đầu chờ nhận video frames

### Bước 5: Khởi tạo Camera và WebRTC (Tùy chọn)

**API tương ứng**: WebRTC peer connection setup

**Mục đích của step này**:
- Thiết lập streaming video real-time từ camera mobile đến server
- Đảm bảo video được truyền với độ trễ thấp và chất lượng ổn định

**Thông tin truyền đi**:
- Video stream từ camera (thông qua WebRTC)
- SDP answer để hoàn tất WebRTC handshake

**Logic xử lý**:
1. Mobile yêu cầu quyền truy cập camera
2. Tạo WebRTC peer connection với STUN servers
3. Thêm video track vào connection
4. Gửi SDP answer để hoàn tất kết nối P2P

### Bước 6: Xử lý WebSocket Messages

**API tương ứng**: WebSocket messages từ server

**Mục đích của step này**:
- Nhận feedback real-time về chất lượng tư thế
- Cập nhật giao diện người dùng với hướng dẫn
- Theo dõi tiến độ hoàn thành bài tập

**Các loại message nhận được**:

**Message "pose_feedback"**:
- `status`: Trạng thái tư thế ("correct", "incorrect", "adjusting")
- `similarity_score`: Độ tương đồng với tư thế chuẩn (0-1)
- `feedback.message`: Thông điệp hướng dẫn bằng tiếng
- `feedback.corrections`: Danh sách gợi ý điều chỉnh cụ thể
- `hold_progress`: Tiến độ giữ tư thế (elapsed, required, percentage)

**Message "task_completed"**:
- `completion_score`: Điểm hoàn thành cuối cùng
- `duration_held`: Thời gian giữ tư thế thành công

**Logic xử lý trên mobile**:
1. Parse JSON message
2. Cập nhật UI với feedback text
3. Hiển thị progress bar cho hold timer
4. Phát âm thanh hoặc hiệu ứng khi hoàn thành

### Bước 7: Stream Frame Data (Nếu không dùng WebRTC)

**API tương ứng**: WebSocket message với type "frame_data"

**Mục đích của step này**:
- Gửi từng frame camera để server xử lý pose detection
- Phương án dự phòng khi WebRTC không khả dụng

**Thông tin truyền đi**:
- `type`: "frame_data"
- `frame_data`: Frame camera encoded base64
- `frame_id`: Số thứ tự frame để tracking

**Logic xử lý**:
- Mobile capture frame từ camera 30fps
- Encode thành JPEG base64
- Gửi qua WebSocket thay vì WebRTC stream

### Bước 8: Đóng Session

**API tương ứng**: WebSocket message với type "end_session"

**Mục đích của step này**:
- Kết thúc phiên làm việc và giải phóng tài nguyên
- Lưu kết quả và thống kê của bài tập
- Cleanup connections để tránh memory leak

**Thông tin truyền đi**:
- `type`: "end_session"

**Logic xử lý trên server**:
1. Dừng xử lý video frames
2. Lưu kết quả cuối cùng vào database
3. Giải phóng MediaPipe detector
4. Đóng WebRTC/WebSocket connections

### Bước 1: Khởi tạo Session Pose Detection

**Endpoint**: `POST /api/tasks/{task_id}/pose-session/start`

**Purpose**: Tạo session mới và nhận thông tin kết nối

#### Request
```javascript
const response = await fetch(`https://api.memotion.com/api/tasks/${taskId}/pose-session/start`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    "exercise_id": "arm_raise_001",
    "stream_type": "webrtc"
  })
});

const sessionData = await response.json();
```

#### Response Thành công
```json
{
  "code": "000",
  "message": "Pose session started successfully",
  "data": {
    "session_id": "session-uuid-12345",
    "webrtc_offer": "webrtc-offer-session-uuid-12345",
    "reference_video_url": "https://api.memotion.com/videos/arm_raise_001.mp4"
  }
}
```

#### Xử lý Lỗi
```javascript
if (sessionData.code !== "000") {
  console.error("Failed to start session:", sessionData.message);
  return;
}

// Lưu session info
const { session_id, webrtc_offer, reference_video_url } = sessionData.data;
```

### Bước 2: Khởi tạo Reference Video

**Purpose**: Load video tham khảo để hiển thị song song với camera

```javascript
// Trong Flutter
_videoController = VideoPlayerController.network(referenceVideoUrl);
await _videoController.initialize();
await _videoController.play();

// Trong Web/JavaScript
const referenceVideo = document.getElementById('reference-video');
referenceVideo.src = referenceVideoUrl;
referenceVideo.play();
```

### Bước 3: Kết nối WebSocket

**URL**: `ws://api.memotion.com/api/tasks/{task_id}/pose-feedback`

**Purpose**: Thiết lập kênh giao tiếp real-time cho feedback

```javascript
// JavaScript WebSocket
const feedbackSocket = new WebSocket(
  `ws://api.memotion.com/api/tasks/${taskId}/pose-feedback`
);

// Flutter WebSocket
final feedbackChannel = WebSocketChannel.connect(
  Uri.parse('ws://api.memotion.com/api/tasks/${taskId}/pose-feedback'),
);
```

### Bước 4: Gửi Start Session Signal

**Purpose**: Thông báo bắt đầu session qua WebSocket

```javascript
// JavaScript
feedbackSocket.onopen = () => {
  feedbackSocket.send(JSON.stringify({
    "type": "start_session",
    "task_id": taskId,
    "exercise_id": "arm_raise_001"
  }));
};

// Flutter
await feedbackChannel.ready;
feedbackChannel.sink.add(json.encode({
  'type': 'start_session',
  'task_id': taskId,
  'exercise_id': 'arm_raise_001'
}));
```

### Bước 5: Khởi tạo Camera và WebRTC (Tùy chọn)

**Purpose**: Stream video real-time từ camera

```javascript
// JavaScript WebRTC Setup
const peerConnection = new RTCPeerConnection({
  iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
});

// Add camera stream
const stream = await navigator.mediaDevices.getUserMedia({
  video: { width: 640, height: 480 }
});
stream.getTracks().forEach(track => {
  peerConnection.addTrack(track, stream);
});

// Set remote description (from session start response)
await peerConnection.setRemoteDescription({
  type: 'offer',
  sdp: webrtcOffer
});

// Create and send answer
const answer = await peerConnection.createAnswer();
await peerConnection.setLocalDescription(answer);
// Send answer to server via signaling server (implementation depends on your setup)
```

### Bước 6: Xử lý WebSocket Messages

**Purpose**: Nhận và xử lý feedback real-time

```javascript
// JavaScript
feedbackSocket.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'pose_feedback':
      handlePoseFeedback(data);
      break;
    case 'task_completed':
      handleTaskCompletion(data);
      break;
    case 'error':
      handleError(data);
      break;
  }
};

function handlePoseFeedback(data) {
  // Update UI với feedback
  updateFeedbackMessage(data.feedback.message);
  updateSimilarityScore(data.similarity_score);
  updateHoldProgress(data.hold_progress.percentage);

  // Hiển thị corrections nếu có
  if (data.feedback.corrections.length > 0) {
    showCorrections(data.feedback.corrections);
  }
}

function handleTaskCompletion(data) {
  // Hiển thị completion dialog
  showCompletionDialog(data.completion_score, data.duration_held);

  // Dừng camera và video
  stopCamera();
  stopReferenceVideo();
}

function handleError(data) {
  console.error('Pose detection error:', data.message);
  showErrorMessage(data.message);
}
```

### Bước 7: Stream Frame Data (Nếu không dùng WebRTC)

**Purpose**: Gửi frame camera để xử lý pose detection

```javascript
// Nếu không dùng WebRTC, gửi frame qua WebSocket
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');

function sendFrame() {
  // Capture frame từ video element
  ctx.drawImage(videoElement, 0, 0, 640, 480);
  const frameData = canvas.toDataURL('image/jpeg', 0.8);

  // Encode to base64 for sending
  const base64Data = frameData.split(',')[1];

  feedbackSocket.send(JSON.stringify({
    "type": "frame_data",
    "frame_data": base64Data,
    "frame_id": frameCount++
  }));

  // Send at 30fps
  setTimeout(sendFrame, 1000/30);
}
```

### Bước 8: Đóng Session

**Purpose**: Kết thúc session và cleanup resources

```javascript
// Gửi end session signal
feedbackSocket.send(JSON.stringify({
  "type": "end_session"
}));

// Đóng connections
feedbackSocket.close();
peerConnection?.close();

// Cleanup Flutter
feedbackChannel.sink.close();
_videoController?.dispose();
_cameraController?.dispose();
```

## Flutter Implementation Example

```dart
class PoseDetectionScreen extends StatefulWidget {
  final String taskId;
  final String exerciseId;

  @override
  _PoseDetectionScreenState createState() => _PoseDetectionScreenState();
}

class _PoseDetectionScreenState extends State<PoseDetectionScreen> {
  late WebSocketChannel _feedbackChannel;
  VideoPlayerController? _referenceController;
  CameraController? _cameraController;

  String _feedbackMessage = '';
  double _similarityScore = 0.0;
  double _holdProgress = 0.0;
  bool _isCompleted = false;

  @override
  void initState() {
    super.initState();
    _initializeSession();
  }

  Future<void> _initializeSession() async {
    try {
      // Bước 1: Start session
      final sessionData = await _startPoseSession();

      // Bước 2: Initialize reference video
      await _initializeReferenceVideo(sessionData['reference_video_url']);

      // Bước 3: Initialize camera
      await _initializeCamera();

      // Bước 4: Setup WebSocket
      _setupWebSocket();

    } catch (e) {
      print('Initialization failed: $e');
    }
  }

  Future<Map<String, dynamic>> _startPoseSession() async {
    final response = await http.post(
      Uri.parse('https://api.memotion.com/api/tasks/${widget.taskId}/pose-session/start'),
      headers: {'Authorization': 'Bearer ${getToken()}'},
      body: json.encode({'exercise_id': widget.exerciseId})
    );

    final data = json.decode(response.body);
    if (data['code'] != '000') {
      throw Exception(data['message']);
    }

    return data['data'];
  }

  Future<void> _initializeReferenceVideo(String url) async {
    _referenceController = VideoPlayerController.network(url);
    await _referenceController!.initialize();
    await _referenceController!.play();
  }

  Future<void> _initializeCamera() async {
    _cameraController = CameraController(
      cameras[0],
      ResolutionPreset.medium
    );
    await _cameraController!.initialize();
  }

  void _setupWebSocket() {
    _feedbackChannel = WebSocketChannel.connect(
      Uri.parse('ws://api.memotion.com/api/tasks/${widget.taskId}/pose-feedback'),
    );

    // Bước 4: Send start signal
    _feedbackChannel.sink.add(json.encode({
      'type': 'start_session',
      'task_id': widget.taskId,
      'exercise_id': widget.exerciseId
    }));

    // Bước 6: Handle messages
    _feedbackChannel.stream.listen((message) {
      final data = json.decode(message);

      setState(() {
        switch(data['type']) {
          case 'pose_feedback':
            _feedbackMessage = data['feedback']['message'];
            _similarityScore = data['similarity_score'];
            _holdProgress = data['hold_progress']['percentage'] / 100.0;
            break;
          case 'task_completed':
            _isCompleted = true;
            _showCompletionDialog();
            break;
        }
      });
    });
  }

  void _showCompletionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Congratulations!'),
        content: Text('Exercise completed successfully!'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Dual video display
          Row(
            children: [
              // User camera
              Expanded(
                child: _cameraController != null
                  ? CameraPreview(_cameraController!)
                  : CircularProgressIndicator(),
              ),
              // Reference video
              Expanded(
                child: _referenceController != null
                  ? AspectRatio(
                      aspectRatio: _referenceController!.value.aspectRatio,
                      child: VideoPlayer(_referenceController!),
                    )
                  : CircularProgressIndicator(),
              ),
            ],
          ),

          // Feedback overlay
          Positioned(
            bottom: 100,
            left: 20,
            right: 20,
            child: Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  Text(
                    _feedbackMessage,
                    style: TextStyle(color: Colors.white, fontSize: 18),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Similarity: ${(_similarityScore * 100).toStringAsFixed(1)}%',
                    style: TextStyle(color: Colors.white),
                  ),
                  LinearProgressIndicator(value: _holdProgress),
                ],
              ),
            ),
          ),

          // Completion overlay
          if (_isCompleted)
            Container(
              color: Colors.black.withOpacity(0.8),
              child: Center(
                child: Text(
                  'Exercise Completed!',
                  style: TextStyle(color: Colors.white, fontSize: 24),
                ),
              ),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    // Bước 8: Cleanup
    _feedbackChannel.sink.close();
    _referenceController?.dispose();
    _cameraController?.dispose();
    super.dispose();
  }
}
```

## Error Handling

### Connection Errors
```javascript
feedbackSocket.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Auto-reconnect logic
  setTimeout(() => connectWebSocket(), 3000);
};

feedbackSocket.onclose = (event) => {
  console.log('WebSocket closed:', event.code, event.reason);
  // Handle reconnection
};
```

### Session Errors
```javascript
// Handle session not found
if (response.status === 404) {
  alert('Session not found. Please restart the exercise.');
}

// Handle authentication errors
if (response.status === 401) {
  redirectToLogin();
}
```

## Performance Optimization

### Frame Rate Control
```javascript
// Limit to 30fps
let lastFrameTime = 0;
const targetFPS = 30;
const frameInterval = 1000 / targetFPS;

function sendFrame(timestamp) {
  if (timestamp - lastFrameTime >= frameInterval) {
    // Send frame
    lastFrameTime = timestamp;
  }
  requestAnimationFrame(sendFrame);
}
```

### Connection Monitoring
```javascript
// Monitor WebSocket health
setInterval(() => {
  if (feedbackSocket.readyState !== WebSocket.OPEN) {
    console.warn('WebSocket connection lost');
    reconnectWebSocket();
  }
}, 5000);
```

## Testing Checklist

- [ ] Session start API returns valid session_id
- [ ] WebSocket connection establishes successfully
- [ ] Reference video loads and plays
- [ ] Camera initializes without errors
- [ ] Frame data sends at correct interval
- [ ] Feedback messages received and parsed
- [ ] Completion detection works
- [ ] Session cleanup on exit
- [ ] Error handling for network issues
- [ ] Memory leaks prevention

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Check firewall settings
   - Verify WebSocket URL format
   - Ensure server is running

2. **Camera access denied**
   - Request camera permissions
   - Check HTTPS requirement for camera access
   - Handle permission denied gracefully

3. **High latency feedback**
   - Reduce frame resolution
   - Optimize frame encoding
   - Check network connection

4. **Session timeout**
   - Implement heartbeat/ping messages
   - Handle reconnection logic
   - Clean up expired sessions

---

**Last Updated**: January 14, 2026
**API Version**: 1.0
**WebSocket Protocol**: JSON over WebSocket</content>
<parameter name="filePath">d:\Innovation\Memotion\POSE_DETECTION_API_GUIDE.md