# CHIẾN LƯỢC TÍCH HỢP POSE DETECTION VỚI MOBILE FLUTTER

## 1. Tổng quan Tích hợp

### 1.1 Mục tiêu
Tích hợp module Pose Detection từ `IEC_MEMOTION/mediapipe` vào backend Memotion (FastAPI) để hỗ trợ mobile Flutter thực hiện bài tập vật lý trị liệu với hướng dẫn real-time và tự động hoàn thành task dựa trên 3 màn hình chính với logic pose detection tự động.

### 1.2 Phạm vi
- **Input**: Mobile stream video realtime từ camera + reference video ID
- **Processing**: Backend xử lý Pose Detection real-time (30fps) qua 3 giai đoạn tự động
- **Output**: Feedback real-time + dual display trên mobile + kết quả phân tích

### 1.3 Logic 3 Màn Hình Chính

**Màn hình 1: Camera và Phát Hiện Tư Thế**
Đây là màn hình đầu tiên khi user mở app. Màn hình này chỉ hiển thị camera của user và thực hiện 2 giai đoạn chính:

**Giai Đoạn 1: Phát Hiện Người (Detection Phase)**
- Camera bật lên hiển thị preview real-time
- Hệ thống phân tích xem có người trong khung hình không
- Đánh giá độ ổn định của tư thế (user có đứng yên và rõ ràng không)
- Khi phát hiện user ổn định (stability score > threshold), tự động chuyển sang giai đoạn tiếp theo mà không cần user làm gì thêm

**Giai Đoạn 2: Thu Thập Cử Động (Measuring Phase)**
- Giai đoạn này sẽ được tự động chuyển sang khi POSE DETECTION phát hiện là user ở giai đoạn 1 đã hoàn thành (tức là user đã vào vị trí, ổn định vị trí)
- Giai đoạn này sẽ có khoảng 10s, user thực hiện các cử động tự do để đo đạt các góc độ, khung khớp, chuẩn bị dữ liệu để bắt đầu màn 2
- User bắt đầu thực hiện bài tập tự do
- Hệ thống thu thập dữ liệu chuyển động qua các khung hình
- Theo dõi quỹ đạo và góc độ của các khớp cơ thể
- Khi thu thập đủ dữ liệu cử động (100+ frames), tự động chuyển sang màn hình tiếp theo

**Màn hình 2: So Sánh với Video Mẫu (Scoring Phase)**
Đây là màn hình chính nơi diễn ra quá trình tập luyện và chấm điểm:
- Hiển thị đồng thời camera của user và video bài tập mẫu
- So sánh cử động của user với bài tập chuẩn theo thời gian thực
- Tính toán các chỉ số: phạm vi chuyển động (ROM), độ ổn định, nhịp độ, tính đối xứng
- Gửi phản hồi tức thì về chất lượng bài tập
- Hiển thị điểm số chi tiết cho từng khía cạnh
- Khi hoàn thành bài tập, chuyển sang màn hình kết quả

**Màn hình 3: Kết Quả và Phân Tích (Results Phase)**
- Hiển thị điểm số tổng thể của bài tập
- Chi tiết điểm cho từng khía cạnh (ROM, stability, flow, symmetry)
- Các đề xuất cải thiện để tập luyện tốt hơn
- Lưu trữ kết quả để theo dõi tiến triển qua thời gian
- Tùy chọn để làm lại bài tập hoặc kết thúc phiên tập

## 2. Kiến trúc Tích hợp

### 2.1 Cấu trúc Thư mục Mở rộng
```
app/
├── api/
│   ├── api_pose_detection.py          # NEW: API cho Pose Detection
│   └── ...
├── services/
│   ├── srv_pose_detection.py          # NEW: Service xử lý Pose Detection
│   └── ...
├── ai_agent/
│   ├── pose_detection_agent.py        # NEW: Wrapper cho mediapipe logic
│   └── ...
└── mediapipe_integration/             # NEW: Copy từ IEC_MEMOTION/mediapipe
    ├── core/
    ├── modules/
    ├── models/
    └── ...
```

### 2.2 Dependencies
Thêm vào `requirements.txt`:
```
opencv-python==4.8.1.78
mediapipe==0.10.7
numpy==1.24.3
scipy==1.11.3
websockets==11.0.3
aiortc==1.6.0  # For WebRTC support
```

## 3. API Design

### 3.1 Tổng quan API Architecture

Hệ thống sử dụng kết hợp REST API và WebSocket để xử lý 3 màn hình pose detection:

- **REST API**: Quản lý session lifecycle (start, get results, end)
- **WebSocket**: Real-time communication cho feedback và phase transitions
- **WebRTC**: Video streaming từ mobile đến backend (optional, có thể dùng WebSocket với base64 frames)

### 3.2 REST API Endpoints

#### 3.2.1 Start Pose Detection Session
**Endpoint**: `POST /api/pose-detection/start-session`

**Tác dụng**: Khởi tạo session pose detection cho một task cụ thể, chuẩn bị cho Màn hình 1.

**Input**:
```json
{
  "task_id": "uuid-of-task",
  "exercise_id": "uuid-of-exercise",
  "user_id": "uuid-of-user",
  "config": {
    "stability_threshold": 0.7,
    "measuring_duration": 10,
    "min_measuring_frames": 100,
    "reference_video_id": "uuid-of-reference-video"
  }
}
```

**Output**:
```json
{
  "code": "000",
  "message": "Session started successfully",
  "data": {
    "session_id": "session-uuid",
    "phase": "detection",
    "reference_video_url": "https://api.memotion.com/videos/exercise-uuid.mp4",
    "websocket_url": "ws://api.memotion.com/pose-detection/session/session-uuid",
    "webrtc_offer": "..." // optional
  }
}
```

**Logic xử lý**:
1. Validate task_id và exercise_id tồn tại
2. Tạo session mới với status = "detection"
3. Khởi tạo pose detector với config
4. Trả về session_id và WebSocket URL để mobile connect
5. Load reference video URL nếu có

#### 3.2.2 Get Session Results
**Endpoint**: `GET /api/pose-detection/session/{session_id}/results`

**Tác dụng**: Lấy kết quả cuối cùng của session sau khi hoàn thành (dùng cho Màn hình 3).

**Input**: 
- Path parameter: `session_id`

**Output**:
```json
{
  "code": "000",
  "data": {
    "session_id": "session-uuid",
    "task_id": "task-uuid",
    "exercise_id": "exercise-uuid",
    "status": "completed",
    "final_scores": {
      "overall_score": 85.5,
      "rom_score": 88.0,
      "stability_score": 82.3,
      "flow_score": 86.7,
      "symmetry_score": 84.1
    },
    "recommendations": [
      "Improve elbow positioning",
      "Increase range of motion",
      "Maintain better balance"
    ],
    "duration": 45.2,
    "completed_at": "2026-01-19T10:30:00Z"
  }
}
```

**Logic xử lý**:
1. Validate session_id và status = "completed"
2. Tính toán final scores từ dữ liệu thu thập
3. Generate recommendations dựa trên scores
4. Update database với kết quả

#### 3.2.3 End Session
**Endpoint**: `POST /api/pose-detection/session/{session_id}/end`

**Tác dụng**: Kết thúc session sớm hoặc cleanup resources.

**Input**:
```json
{
  "reason": "user_cancelled" // optional
}
```

**Output**:
```json
{
  "code": "000",
  "message": "Session ended successfully"
}
```

**Logic xử lý**:
1. Update session status = "ended"
2. Cleanup resources (pose detector, WebSocket connections)
3. Save partial results nếu có

### 3.3 WebSocket API cho Real-time Communication

**URL**: `ws://api/pose-detection/session/{session_id}`

**Tác dụng**: Xử lý real-time communication giữa mobile và backend qua các giai đoạn của 3 màn hình.

#### 3.3.1 Message Types và Flow

**Client → Server Messages:**

1. **Start Session Confirmation**
```json
{
  "type": "start_session",
  "session_id": "session-uuid",
  "device_info": {
    "platform": "ios|android",
    "camera_resolution": "640x480"
  }
}
```

2. **Frame Data (Detection & Measuring Phases)**
```json
{
  "type": "frame_data",
  "frame_id": 123,
  "timestamp": 1234567890,
  "image_data": "base64-encoded-jpeg",
  "phase": "detection|measuring"
}
```

3. **Phase Transition Request (Manual)**
```json
{
  "type": "request_phase_change",
  "current_phase": "measuring",
  "target_phase": "scoring"
}
```

**Server → Client Messages:**

1. **Phase Change Notification**
```json
{
  "type": "phase_change",
  "phase": "detection|measuring|scoring|completed",
  "message": "Moving to measuring phase...",
  "timestamp": 1234567890
}
```

2. **Detection Phase Feedback**
```json
{
  "type": "detection_feedback",
  "person_detected": true,
  "stability_score": 0.85,
  "feedback_message": "Please stand still and face the camera",
  "frames_stable": 15,
  "required_stable_frames": 30
}
```

3. **Measuring Phase Feedback**
```json
{
  "type": "measuring_feedback",
  "frames_captured": 67,
  "total_required_frames": 100,
  "progress_percentage": 67,
  "feedback_message": "Keep moving naturally...",
  "landmarks_collected": 150
}
```

4. **Scoring Phase Feedback**
```json
{
  "type": "scoring_feedback",
  "similarity_score": 87.3,
  "scores": {
    "rom_score": 89.0,
    "stability_score": 85.2,
    "flow_score": 88.1,
    "symmetry_score": 86.5
  },
  "feedback_message": "Excellent form! Keep it up",
  "corrections": [
    {"joint": "left_elbow", "action": "raise_higher", "angle_diff": 12}
  ],
  "hold_progress": {
    "current_seconds": 3.2,
    "required_seconds": 5.0,
    "percentage": 64
  }
}
```

5. **Exercise Completed**
```json
{
  "type": "exercise_completed",
  "final_scores": {
    "overall_score": 92.5,
    "rom_score": 94.0,
    "stability_score": 91.2,
    "flow_score": 93.1,
    "symmetry_score": 92.5
  },
  "duration": 45.2,
  "recommendations": ["Great job!", "Try to maintain symmetry"]
}
```

6. **Error Messages**
```json
{
  "type": "error",
  "error_code": "NO_PERSON_DETECTED",
  "message": "No person detected in frame",
  "suggestion": "Please stand in front of camera"
}
```

#### 3.3.2 Logic Xử lý WebSocket

**Detection Phase Logic**:
1. Nhận frame_data từ client
2. Chạy pose detection để kiểm tra có người không
3. Tính stability score dựa trên pose consistency qua frames
4. Khi đủ stable frames (30 frames liên tiếp > threshold), tự động chuyển sang measuring phase
5. Gửi detection_feedback mỗi frame

**Measuring Phase Logic**:
1. Thu thập frames và extract pose landmarks
2. Tính toán joint angles và movement trajectories
3. Theo dõi progress (frames_captured / required_frames)
4. Khi đủ frames (100+), tự động chuyển sang scoring phase
5. Gửi measuring_feedback mỗi frame

**Scoring Phase Logic**:
1. Load reference pose sequence từ video mẫu
2. So sánh real-time pose với reference poses
3. Tính similarity scores và corrections
4. Track hold time cho completion
5. Khi hold đủ lâu (5s), mark completed và chuyển sang results
6. Gửi scoring_feedback mỗi frame

### 3.4 Error Handling

**Common Error Codes**:
- `INVALID_SESSION`: Session không tồn tại hoặc expired
- `PHASE_TRANSITION_INVALID`: Chuyển phase không hợp lệ
- `FRAME_PROCESSING_FAILED`: Lỗi xử lý frame
- `REFERENCE_VIDEO_NOT_FOUND`: Video mẫu không tìm thấy
- `POSE_DETECTION_FAILED`: MediaPipe detection lỗi

## 4. Logic Xử lý Real-time

### 4.1 Video Streaming Architecture
```
Mobile App (Flutter)          Backend (FastAPI)
    |                              |
    +--- WebSocket Stream ------->+
    |   (Camera frames 30fps)      |
    |                              |
    +<--- Reference Video URL -----+
    |                              |
    +--- WebSocket --------------->+
    |   (Control messages)         |
    +<--- Feedback Stream ---------+
         (30fps pose analysis)
```

### 4.2 Real-time Processing Pipeline
```python
class RealTimePoseDetectionService:
    def __init__(self):
        self.detector = MediaPipePoseDetector()
        self.active_sessions = {}
        self.phase_handlers = {
            'detection': self._handle_detection_phase,
            'measuring': self._handle_measuring_phase,
            'scoring': self._handle_scoring_phase
        }
    
    async def process_frame(self, session_id: str, frame_data: str, phase: str):
        """Main frame processing entry point"""
        # Decode base64 frame
        frame_bytes = base64.b64decode(frame_data)
        frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # Get session data
        session = self.active_sessions[session_id]
        
        # Route to appropriate phase handler
        handler = self.phase_handlers.get(phase, self._handle_unknown_phase)
        result = await handler(session, frame)
        
        # Send feedback via WebSocket
        await self.send_feedback(session_id, result)
        
        # Check for phase transitions
        await self._check_phase_transitions(session_id, result)
    
    async def _handle_detection_phase(self, session, frame):
        """Detection Phase: Check for person and stability"""
        # Run pose detection
        pose_result = self.detector.process_frame(frame)
        
        if not pose_result.pose_landmarks:
            return {
                'type': 'detection_feedback',
                'person_detected': False,
                'stability_score': 0.0,
                'feedback_message': 'No person detected. Please stand in front of camera.',
                'frames_stable': 0,
                'required_stable_frames': 30
            }
        
        # Calculate stability score
        stability = self._calculate_stability_score(session, pose_result.pose_landmarks)
        session['stability_scores'].append(stability)
        
        # Check if stable enough
        stable_frames = sum(1 for s in session['stability_scores'][-30:] if s > 0.7)
        
        if stable_frames >= 30:
            # Ready for measuring phase
            session['phase'] = 'measuring'
            session['measuring_start'] = time.time()
            await self._notify_phase_change(session['session_id'], 'measuring')
        
        return {
            'type': 'detection_feedback',
            'person_detected': True,
            'stability_score': stability,
            'feedback_message': f'Stability: {stability:.1%}. Please stand still.',
            'frames_stable': stable_frames,
            'required_stable_frames': 30
        }
    
    async def _handle_measuring_phase(self, session, frame):
        """Measuring Phase: Collect movement data"""
        pose_result = self.detector.process_frame(frame)
        
        if pose_result.pose_landmarks:
            # Store landmarks and calculate angles
            session['landmarks'].append(pose_result.pose_landmarks)
            angles = self._calculate_joint_angles(pose_result.pose_landmarks)
            session['angles'].append(angles)
        
        frames_captured = len(session['landmarks'])
        total_required = session.get('min_measuring_frames', 100)
        progress = min(frames_captured / total_required, 1.0)
        
        if frames_captured >= total_required:
            # Ready for scoring phase
            session['phase'] = 'scoring'
            session['scoring_start'] = time.time()
            await self._notify_phase_change(session['session_id'], 'scoring')
        
        return {
            'type': 'measuring_feedback',
            'frames_captured': frames_captured,
            'total_required_frames': total_required,
            'progress_percentage': progress * 100,
            'feedback_message': f'Collecting data... {frames_captured}/{total_required} frames',
            'landmarks_collected': len(session['landmarks'])
        }
    
    async def _handle_scoring_phase(self, session, frame):
        """Scoring Phase: Compare with reference and score"""
        pose_result = self.detector.process_frame(frame)
        
        if not pose_result.pose_landmarks:
            return {
                'type': 'scoring_feedback',
                'similarity_score': 0.0,
                'scores': {},
                'feedback_message': 'Lost pose detection. Please readjust.',
                'corrections': [],
                'hold_progress': {'percentage': 0}
            }
        
        # Compare with reference poses
        reference_poses = session.get('reference_poses', [])
        similarity_scores = []
        
        for ref_pose in reference_poses:
            similarity = self._calculate_pose_similarity(pose_result.pose_landmarks, ref_pose)
            similarity_scores.append(similarity)
        
        avg_similarity = np.mean(similarity_scores) if similarity_scores else 0.0
        
        # Calculate detailed scores
        scores = self._calculate_detailed_scores(session, pose_result.pose_landmarks, avg_similarity)
        
        # Update hold timer
        hold_status = self._update_hold_timer(session, avg_similarity > 0.8)
        
        # Generate corrections
        corrections = self._generate_corrections(pose_result.pose_landmarks, reference_poses[0] if reference_poses else None)
        
        feedback_msg = self._generate_feedback_message(avg_similarity, corrections)
        
        if hold_status['completed']:
            await self._complete_exercise(session)
        
        return {
            'type': 'scoring_feedback',
            'similarity_score': avg_similarity,
            'scores': scores,
            'feedback_message': feedback_msg,
            'corrections': corrections,
            'hold_progress': hold_status
        }
    
    def _calculate_stability_score(self, session, landmarks):
        """Calculate pose stability based on landmark consistency"""
        if len(session.get('previous_landmarks', [])) < 5:
            session.setdefault('previous_landmarks', []).append(landmarks)
            return 0.5
        
        # Compare with recent frames
        recent_landmarks = session['previous_landmarks'][-5:]
        stability_scores = []
        
        for prev_landmarks in recent_landmarks:
            stability = self._calculate_pose_similarity(landmarks, prev_landmarks)
            stability_scores.append(stability)
        
        session['previous_landmarks'].append(landmarks)
        return np.mean(stability_scores)
    
    def _calculate_joint_angles(self, landmarks):
        """Calculate key joint angles"""
        # Implementation for calculating angles at key joints
        # Left elbow, right elbow, left shoulder, right shoulder, etc.
        return {}  # Placeholder
    
    def _calculate_pose_similarity(self, pose1, pose2):
        """Calculate similarity between two poses"""
        # Use MediaPipe's pose similarity or custom implementation
        return 0.85  # Placeholder
    
    def _calculate_detailed_scores(self, session, landmarks, similarity):
        """Calculate ROM, stability, flow, symmetry scores"""
        return {
            'rom_score': similarity * 0.9,
            'stability_score': similarity * 0.95,
            'flow_score': similarity * 0.85,
            'symmetry_score': similarity * 0.8
        }
    
    def _update_hold_timer(self, session, is_correct_pose):
        """Track hold time for exercise completion"""
        if is_correct_pose:
            if 'hold_start' not in session:
                session['hold_start'] = time.time()
            
            elapsed = time.time() - session['hold_start']
            required = 5.0  # 5 seconds
            
            if elapsed >= required:
                return {
                    'current_seconds': elapsed,
                    'required_seconds': required,
                    'percentage': 100,
                    'completed': True
                }
            else:
                return {
                    'current_seconds': elapsed,
                    'required_seconds': required,
                    'percentage': (elapsed / required) * 100,
                    'completed': False
                }
        else:
            session.pop('hold_start', None)
            return {
                'current_seconds': 0,
                'required_seconds': 5.0,
                'percentage': 0,
                'completed': False
            }
    
    async def _check_phase_transitions(self, session_id, result):
        """Check and handle automatic phase transitions"""
        session = self.active_sessions[session_id]
        
        if result.get('type') == 'detection_feedback' and result.get('frames_stable', 0) >= 30:
            await self._notify_phase_change(session_id, 'measuring')
        
        elif result.get('type') == 'measuring_feedback' and result.get('progress_percentage', 0) >= 100:
            await self._notify_phase_change(session_id, 'scoring')
        
        elif result.get('type') == 'scoring_feedback' and result.get('hold_progress', {}).get('completed', False):
            await self._notify_phase_change(session_id, 'completed')
    
    async def _notify_phase_change(self, session_id, new_phase):
        """Notify client of phase change"""
        await self.send_feedback(session_id, {
            'type': 'phase_change',
            'phase': new_phase,
            'message': f'Moving to {new_phase} phase...',
            'timestamp': int(time.time() * 1000)
        })
    
    async def _complete_exercise(self, session):
        """Handle exercise completion"""
        final_scores = self._calculate_final_scores(session)
        recommendations = self._generate_recommendations(session, final_scores)
        
        await self.send_feedback(session['session_id'], {
            'type': 'exercise_completed',
            'final_scores': final_scores,
            'duration': time.time() - session['scoring_start'],
            'recommendations': recommendations
        })
        
        # Save results to database
        await self._save_results(session, final_scores, recommendations)
```

## 5. Mobile Flutter Implementation

### 5.1 Cấu trúc 3 Màn Hình

Ứng dụng Flutter sẽ có 3 màn hình riêng biệt với navigation tự động dựa trên phase changes từ backend:

```dart
class PoseDetectionFlow extends StatefulWidget {
  final String taskId;
  final String exerciseId;

  @override
  _PoseDetectionFlowState createState() => _PoseDetectionFlowState();
}

class _PoseDetectionFlowState extends State<PoseDetectionFlow> {
  String _currentPhase = 'detection'; // detection -> measuring -> scoring -> completed
  String _sessionId = '';
  WebSocketChannel? _webSocketChannel;

  @override
  void initState() {
    super.initState();
    _initializeSession();
  }

  Future<void> _initializeSession() async {
    // Start session via REST API
    final response = await http.post(
      Uri.parse('${Config.apiBaseUrl}/api/pose-detection/start-session'),
      headers: {'Authorization': 'Bearer ${getToken()}'},
      body: json.encode({
        'task_id': widget.taskId,
        'exercise_id': widget.exerciseId,
        'config': {
          'stability_threshold': 0.7,
          'measuring_duration': 10,
          'min_measuring_frames': 100
        }
      })
    );

    final data = json.decode(response.body)['data'];
    _sessionId = data['session_id'];

    // Connect WebSocket
    _setupWebSocket();
  }

  void _setupWebSocket() {
    _webSocketChannel = WebSocketChannel.connect(
      Uri.parse('${Config.wsBaseUrl}/api/pose-detection/session/$_sessionId'),
    );

    _webSocketChannel?.stream.listen((message) {
      final data = json.decode(message);
      _handleWebSocketMessage(data);
    });

    // Send start confirmation
    _webSocketChannel?.sink.add(json.encode({
      'type': 'start_session',
      'session_id': _sessionId,
      'device_info': {'platform': Platform.isIOS ? 'ios' : 'android'}
    }));
  }

  void _handleWebSocketMessage(Map<String, dynamic> data) {
    switch (data['type']) {
      case 'phase_change':
        setState(() {
          _currentPhase = data['phase'];
        });
        break;
      // Handle other message types...
    }
  }

  Widget _buildCurrentScreen() {
    switch (_currentPhase) {
      case 'detection':
        return DetectionScreen(sessionId: _sessionId, webSocket: _webSocketChannel);
      case 'measuring':
        return MeasuringScreen(sessionId: _sessionId, webSocket: _webSocketChannel);
      case 'scoring':
        return ScoringScreen(sessionId: _sessionId, webSocket: _webSocketChannel);
      case 'completed':
        return ResultsScreen(sessionId: _sessionId);
      default:
        return LoadingScreen();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _buildCurrentScreen(),
    );
  }
}
```

### 5.2 Màn Hình 1: Detection Screen

```dart
class DetectionScreen extends StatefulWidget {
  final String sessionId;
  final WebSocketChannel? webSocket;

  @override
  _DetectionScreenState createState() => _DetectionScreenState();
}

class _DetectionScreenState extends State<DetectionScreen> {
  CameraController? _cameraController;
  Timer? _frameTimer;
  String _feedbackMessage = 'Please stand in front of the camera';
  double _stabilityScore = 0.0;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _startFrameCapture();
  }

  Future<void> _initializeCamera() async {
    _cameraController = CameraController(cameras[0], ResolutionPreset.medium);
    await _cameraController?.initialize();
    setState(() {});
  }

  void _startFrameCapture() {
    _frameTimer = Timer.periodic(Duration(milliseconds: 33), (timer) async { // 30fps
      if (_cameraController != null && _cameraController!.value.isInitialized) {
        final image = await _cameraController!.takePicture();
        final bytes = await image.readAsBytes();
        final base64Image = base64Encode(bytes);

        widget.webSocket?.sink.add(json.encode({
          'type': 'frame_data',
          'frame_id': DateTime.now().millisecondsSinceEpoch,
          'timestamp': DateTime.now().millisecondsSinceEpoch,
          'image_data': base64Image,
          'phase': 'detection'
        }));
      }
    });
  }

  void _handleWebSocketMessage(Map<String, dynamic> data) {
    if (data['type'] == 'detection_feedback') {
      setState(() {
        _feedbackMessage = data['feedback_message'];
        _stabilityScore = data['stability_score'];
      });
    } else if (data['type'] == 'phase_change' && data['phase'] == 'measuring') {
      _frameTimer?.cancel();
      // Auto navigate to measuring screen
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Pose Detection - Detection Phase')),
      body: Column(
        children: [
          Expanded(
            child: _cameraController != null && _cameraController!.value.isInitialized
              ? CameraPreview(_cameraController!)
              : Center(child: CircularProgressIndicator()),
          ),
          Container(
            padding: EdgeInsets.all(16),
            color: Colors.black.withOpacity(0.7),
            child: Column(
              children: [
                Text(_feedbackMessage, style: TextStyle(color: Colors.white, fontSize: 18)),
                SizedBox(height: 8),
                Text('Stability: ${(_stabilityScore * 100).toStringAsFixed(1)}%',
                     style: TextStyle(color: Colors.white)),
                LinearProgressIndicator(value: _stabilityScore, backgroundColor: Colors.grey),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _frameTimer?.cancel();
    _cameraController?.dispose();
    super.dispose();
  }
}
```

### 5.3 Màn Hình 2: Measuring Screen

```dart
class MeasuringScreen extends StatefulWidget {
  final String sessionId;
  final WebSocketChannel? webSocket;

  @override
  _MeasuringScreenState createState() => _MeasuringScreenState();
}

class _MeasuringScreenState extends State<MeasuringScreen> {
  CameraController? _cameraController;
  Timer? _frameTimer;
  String _feedbackMessage = 'Move naturally to collect pose data';
  int _framesCaptured = 0;
  int _totalRequired = 100;
  double _progress = 0.0;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _startFrameCapture();
  }

  // Similar camera initialization as DetectionScreen

  void _startFrameCapture() {
    _frameTimer = Timer.periodic(Duration(milliseconds: 33), (timer) async {
      // Send frames with phase: 'measuring'
      widget.webSocket?.sink.add(json.encode({
        'type': 'frame_data',
        'phase': 'measuring',
        // ... frame data
      }));
    });
  }

  void _handleWebSocketMessage(Map<String, dynamic> data) {
    if (data['type'] == 'measuring_feedback') {
      setState(() {
        _framesCaptured = data['frames_captured'];
        _progress = data['progress_percentage'] / 100.0;
        _feedbackMessage = data['feedback_message'];
      });
    } else if (data['type'] == 'phase_change' && data['phase'] == 'scoring') {
      _frameTimer?.cancel();
      // Auto navigate to scoring screen
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Pose Detection - Measuring Phase')),
      body: Column(
        children: [
          Expanded(child: CameraPreview(_cameraController!)),
          Container(
            padding: EdgeInsets.all(16),
            color: Colors.black.withOpacity(0.7),
            child: Column(
              children: [
                Text(_feedbackMessage, style: TextStyle(color: Colors.white, fontSize: 18)),
                SizedBox(height: 8),
                Text('Progress: $_framesCaptured / $_totalRequired frames',
                     style: TextStyle(color: Colors.white)),
                LinearProgressIndicator(value: _progress, backgroundColor: Colors.grey),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

### 5.4 Màn Hình 3: Scoring Screen

```dart
class ScoringScreen extends StatefulWidget {
  final String sessionId;
  final WebSocketChannel? webSocket;

  @override
  _ScoringScreenState createState() => _ScoringScreenState();
}

class _ScoringScreenState extends State<ScoringScreen> {
  CameraController? _cameraController;
  VideoPlayerController? _referenceController;
  Timer? _frameTimer;
  
  String _feedbackMessage = '';
  double _similarityScore = 0.0;
  Map<String, double> _scores = {};
  double _holdProgress = 0.0;

  @override
  void initState() {
    super.initState();
    _initializeCameraAndVideo();
    _startFrameCapture();
  }

  Future<void> _initializeCameraAndVideo() async {
    // Initialize camera
    _cameraController = CameraController(cameras[0], ResolutionPreset.medium);
    await _cameraController?.initialize();

    // Initialize reference video
    _referenceController = VideoPlayerController.network('reference_video_url');
    await _referenceController?.initialize();
    await _referenceController?.play();

    setState(() {});
  }

  void _startFrameCapture() {
    _frameTimer = Timer.periodic(Duration(milliseconds: 33), (timer) async {
      // Send frames with phase: 'scoring'
      // Note: No frame data sent in scoring phase, backend uses reference comparison
    });
  }

  void _handleWebSocketMessage(Map<String, dynamic> data) {
    if (data['type'] == 'scoring_feedback') {
      setState(() {
        _feedbackMessage = data['feedback_message'];
        _similarityScore = data['similarity_score'];
        _scores = Map<String, double>.from(data['scores']);
        _holdProgress = data['hold_progress']['percentage'] / 100.0;
      });
    } else if (data['type'] == 'exercise_completed') {
      _frameTimer?.cancel();
      // Navigate to results screen
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => ResultsScreen(sessionId: widget.sessionId)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Pose Detection - Scoring Phase')),
      body: Column(
        children: [
          Row(
            children: [
              Expanded(child: CameraPreview(_cameraController!)),
              Expanded(
                child: _referenceController != null && _referenceController!.value.isInitialized
                  ? AspectRatio(
                      aspectRatio: _referenceController!.value.aspectRatio,
                      child: VideoPlayer(_referenceController!),
                    )
                  : Center(child: CircularProgressIndicator()),
              ),
            ],
          ),
          Container(
            padding: EdgeInsets.all(16),
            color: Colors.black.withOpacity(0.7),
            child: Column(
              children: [
                Text(_feedbackMessage, style: TextStyle(color: Colors.white, fontSize: 18)),
                SizedBox(height: 8),
                Text('Similarity: ${(_similarityScore * 100).toStringAsFixed(1)}%',
                     style: TextStyle(color: Colors.white)),
                LinearProgressIndicator(value: _holdProgress, backgroundColor: Colors.grey),
                Text('Hold Progress: ${(_holdProgress * 100).toStringAsFixed(0)}%',
                     style: TextStyle(color: Colors.white)),
                // Display detailed scores
                if (_scores.isNotEmpty) ...[
                  SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: _scores.entries.map((entry) =>
                      Text('${entry.key}: ${(entry.value * 100).toStringAsFixed(0)}%',
                           style: TextStyle(color: Colors.white, fontSize: 12))
                    ).toList(),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

### 5.5 Màn Hình 4: Results Screen

```dart
class ResultsScreen extends StatefulWidget {
  final String sessionId;

  @override
  _ResultsScreenState createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  Map<String, dynamic>? _results;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadResults();
  }

  Future<void> _loadResults() async {
    final response = await http.get(
      Uri.parse('${Config.apiBaseUrl}/api/pose-detection/session/${widget.sessionId}/results'),
      headers: {'Authorization': 'Bearer ${getToken()}'},
    );

    setState(() {
      _results = json.decode(response.body)['data'];
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final scores = _results!['final_scores'];
    final recommendations = List<String>.from(_results!['recommendations']);

    return Scaffold(
      appBar: AppBar(title: Text('Exercise Results')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Overall Score: ${(scores['overall_score'] * 100).toStringAsFixed(1)}%',
                 style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            Text('Detailed Scores:', style: TextStyle(fontSize: 18)),
            SizedBox(height: 8),
            ...scores.entries.where((e) => e.key != 'overall_score').map((entry) =>
              Padding(
                padding: EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(entry.key.replaceAll('_', ' ').toUpperCase()),
                    Text('${(entry.value * 100).toStringAsFixed(1)}%'),
                  ],
                ),
              )
            ),
            SizedBox(height: 16),
            Text('Recommendations:', style: TextStyle(fontSize: 18)),
            SizedBox(height: 8),
            ...recommendations.map((rec) =>
              Padding(
                padding: EdgeInsets.symmetric(vertical: 2),
                child: Text('• $rec'),
              )
            ),
            Spacer(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('Do Again'),
                ),
                ElevatedButton(
                  onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
                  child: Text('Finish'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
```

## 6. Backend Implementation Steps

### Phase 1: Session Management Setup
1. Implement REST API endpoints (`/api/pose-detection/start-session`, `/session/{id}/results`, `/session/{id}/end`)
2. Setup session storage (Redis/database) với lifecycle tracking
3. Initialize pose detection models và config

### Phase 2: WebSocket Handler Implementation
1. Implement WebSocket endpoint `/api/pose-detection/session/{session_id}`
2. Handle message routing cho các phase (detection, measuring, scoring)
3. Setup frame processing pipeline với MediaPipe

### Phase 3: Detection Phase Logic
1. Process incoming frames từ WebSocket
2. Run pose detection để kiểm tra person presence
3. Calculate stability score dựa trên pose consistency
4. Auto-transition to measuring phase khi đủ stable frames

### Phase 4: Measuring Phase Logic
1. Collect pose landmarks từ frames
2. Calculate joint angles và movement trajectories
3. Track progress và send feedback
4. Auto-transition to scoring phase khi đủ data

### Phase 5: Scoring Phase Logic
1. Load reference pose sequence từ exercise config
2. Real-time comparison với user poses
3. Calculate detailed scores (ROM, stability, flow, symmetry)
4. Track hold time cho completion
5. Khi hold đủ lâu (5s), mark completed và chuyển sang results

### Phase 6: Results Processing
1. Aggregate final scores từ scoring phase
2. Generate recommendations dựa trên performance
3. Save results to database
4. Cleanup session resources

## 7. Performance Optimization

### 7.1 Frame Processing
- **Frame Rate**: 30fps input, process every frame
- **Resolution**: 640x480 đủ cho pose detection
- **Compression**: Base64 encoding cho WebSocket transport

### 7.2 Backend Scaling
- **Async Processing**: Use asyncio cho concurrent sessions
- **GPU Acceleration**: MediaPipe hỗ trợ GPU
- **Horizontal Scaling**: Multiple worker instances với load balancer

### 7.3 Mobile Optimization
- **Battery**: 30fps frame capture với optimization
- **Network**: WebSocket với binary frame data
- **UI**: Smooth phase transitions và real-time updates

## 8. Error Handling & Recovery

### 8.1 Connection Issues
- **WebSocket Disconnect**: Auto-reconnect với exponential backoff
- **Session Timeout**: Cleanup expired sessions
- **Network Issues**: Graceful degradation với cached feedback

### 8.2 Processing Errors
- **Pose Detection Fail**: Fallback với basic person detection
- **Frame Decode Error**: Skip corrupted frames
- **Memory Issues**: Limit concurrent sessions per instance

## 9. Testing Strategy

### 9.1 Unit Tests
- Pose detection accuracy với test images
- Phase transition logic
- Score calculation algorithms
- WebSocket message handling

### 9.2 Integration Tests
- End-to-end session flow (start → detection → measuring → scoring → results)
- WebSocket communication với mock frames
- REST API endpoints validation

### 9.3 Performance Tests
- Concurrent sessions (10-50 users)
- Frame processing latency (<33ms per frame)
- Memory usage và resource cleanup

---

**Tác giả**: AI Assistant  
**Ngày**: January 19, 2026  
**Version**: 3.0 (3-Phase Pose Detection)</content>
<parameter name="filePath">d:\Innovation\Memotion\POSE_DETECTION_INTEGRATION_STRATEGY.md