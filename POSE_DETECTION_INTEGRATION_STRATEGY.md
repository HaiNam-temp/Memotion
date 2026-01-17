# CHIẾN LƯỢC TÍCH HỢP POSE DETECTION VỚI MOBILE FLUTTER

## 1. Tổng quan Tích hợp

### 1.1 Mục tiêu
Tích hợp module Pose Detection từ `IEC_MEMOTION/mediapipe` vào backend Memotion (FastAPI) để hỗ trợ mobile Flutter thực hiện bài tập vật lý trị liệu với hướng dẫn real-time và tự động hoàn thành task.

### 1.2 Phạm vi
- **Input**: Mobile stream video realtime từ camera + reference video ID
- **Processing**: Backend xử lý Pose Detection real-time (30fps)
- **Output**: Feedback real-time + dual display trên mobile

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

### 3.1 WebRTC Signaling cho Video Streaming

**Endpoint**: `POST /api/tasks/{task_id}/pose-session/start`

**Purpose**: Khởi tạo session pose detection, trả về WebRTC credentials

#### Request Body
```json
{
  "exercise_id": "uuid-of-exercise",
  "stream_type": "webrtc"
}
```

#### Response
```json
{
  "code": "000",
  "data": {
    "session_id": "session-uuid",
    "webrtc_offer": "...",
    "reference_video_url": "https://api.memotion.com/videos/exercise-uuid.mp4"
  }
}
```

### 3.2 WebSocket cho Real-time Feedback

**URL**: `ws://api/tasks/{task_id}/pose-feedback`

**Protocol**: JSON messages với 30fps update

#### Message Flow
```json
// Client → Server (start session)
{
  "type": "start_session",
  "task_id": "uuid",
  "exercise_id": "uuid"
}

// Server → Client (real-time feedback)
{
  "type": "pose_feedback",
  "timestamp": 1234567890,
  "frame_id": 45,
  "status": "correct|incorrect|adjusting",
  "similarity_score": 87.3,
  "feedback": {
    "message": "Good posture! Hold for 3 more seconds",
    "corrections": [
      {"joint": "left_elbow", "action": "raise_higher", "angle_diff": 15}
    ]
  },
  "hold_progress": {
    "current_seconds": 2.1,
    "required_seconds": 5.0,
    "percentage": 42
  }
}

// Server → Client (task completion)
{
  "type": "task_completed",
  "task_id": "uuid",
  "completion_score": 92.5,
  "duration_held": 5.2
}
```

## 4. Logic Xử lý Real-time

### 4.1 Video Streaming Architecture
```
Mobile App (Flutter)          Backend (FastAPI)
    |                              |
    +--- WebRTC Stream ---------->+
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
        self.detector = VisionDetector(config)
        self.reference_poses = {}  # Cache reference poses
        self.active_sessions = {}
    
    async def process_frame_stream(self, session_id: str, frame_data: bytes):
        """Process incoming video frame from WebRTC"""
        # Decode frame
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Detect pose
        result = self.detector.process_frame(frame, timestamp_ms=time.time()*1000)
        
        # Get reference pose for current exercise phase
        ref_pose = self.get_current_reference_pose(session_id)
        
        # Analyze pose
        feedback = self.analyze_pose(result.pose_landmarks, ref_pose)
        
        # Update hold timer
        hold_status = self.update_hold_timer(session_id, feedback)
        
        # Send feedback via WebSocket
        await self.send_feedback(session_id, feedback, hold_status)
        
        # Check completion
        if hold_status['completed']:
            await self.complete_task(session_id)
    
    def analyze_pose(self, user_pose, ref_pose):
        """Analyze pose similarity and generate feedback"""
        similarity = compute_procrustes_similarity(user_pose, ref_pose)
        
        if similarity < 0.7:
            corrections = self.generate_corrections(user_pose, ref_pose)
            return {
                "status": "incorrect",
                "similarity_score": similarity,
                "feedback": {
                    "message": f"Adjust your {corrections[0]['joint']}",
                    "corrections": corrections
                }
            }
        else:
            return {
                "status": "correct",
                "similarity_score": similarity,
                "feedback": {
                    "message": "Perfect! Hold this position",
                    "corrections": []
                }
            }
    
    def update_hold_timer(self, session_id, feedback):
        """Track how long user holds correct pose"""
        session = self.active_sessions[session_id]
        
        if feedback['status'] == 'correct':
            session['hold_start'] = session.get('hold_start', time.time())
            elapsed = time.time() - session['hold_start']
            
            if elapsed >= 5.0:  # 5 second hold required
                return {
                    "holding": True,
                    "elapsed": elapsed,
                    "required": 5.0,
                    "percentage": 100,
                    "completed": True
                }
            else:
                return {
                    "holding": True,
                    "elapsed": elapsed,
                    "required": 5.0,
                    "percentage": (elapsed / 5.0) * 100,
                    "completed": False
                }
        else:
            session['hold_start'] = None
            return {
                "holding": False,
                "elapsed": 0,
                "required": 5.0,
                "percentage": 0,
                "completed": False
            }
```

## 5. Mobile Flutter Implementation

### 5.1 Dual Display UI
```dart
class PoseDetectionScreen extends StatefulWidget {
  final String taskId;
  final String exerciseId;
  
  @override
  _PoseDetectionScreenState createState() => _PoseDetectionScreenState();
}

class _PoseDetectionScreenState extends State<PoseDetectionScreen> {
  CameraController? _cameraController;
  VideoPlayerController? _referenceController;
  WebSocketChannel? _feedbackChannel;
  RTCPeerConnection? _peerConnection;
  
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
    // Start pose detection session
    final sessionData = await _startPoseSession();
    
    // Initialize reference video
    _referenceController = VideoPlayerController.network(sessionData['reference_video_url']);
    await _referenceController?.initialize();
    await _referenceController?.play();
    
    // Initialize camera
    _cameraController = CameraController(cameras[0], ResolutionPreset.medium);
    await _cameraController?.initialize();
    
    // Setup WebRTC
    await _setupWebRTC(sessionData['webrtc_offer']);
    
    // Setup WebSocket
    _setupWebSocket();
  }
  
  Future<Map<String, dynamic>> _startPoseSession() async {
    final response = await http.post(
      Uri.parse('https://api.memotion.com/api/tasks/${widget.taskId}/pose-session/start'),
      headers: {'Authorization': 'Bearer ${getToken()}'},
      body: json.encode({'exercise_id': widget.exerciseId})
    );
    return json.decode(response.body)['data'];
  }
  
  void _setupWebSocket() {
    _feedbackChannel = WebSocketChannel.connect(
      Uri.parse('ws://api.memotion.com/api/tasks/${widget.taskId}/pose-feedback'),
    );
    
    _feedbackChannel?.stream.listen((message) {
      final data = json.decode(message);
      setState(() {
        _feedbackMessage = data['feedback']['message'];
        _similarityScore = data['similarity_score'];
        _holdProgress = data['hold_progress']['percentage'] / 100.0;
        
        if (data['type'] == 'task_completed') {
          _isCompleted = true;
          _showCompletionDialog();
        }
      });
    });
    
    // Send start signal
    _feedbackChannel?.sink.add(json.encode({
      'type': 'start_session',
      'task_id': widget.taskId,
      'exercise_id': widget.exerciseId
    }));
  }
  
  Future<void> _setupWebRTC(String offer) async {
    _peerConnection = await createPeerConnection({
      'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]
    });
    
    // Add camera stream
    final stream = await _cameraController?.initialize();
    stream?.getTracks().forEach((track) {
      _peerConnection?.addTrack(track, stream);
    });
    
    // Handle remote stream (if needed)
    _peerConnection?.onTrack = (event) {
      // Handle incoming stream if backend sends back processed video
    };
    
    // Set remote description and create answer
    await _peerConnection?.setRemoteDescription(
      RTCSessionDescription(offer, 'offer')
    );
    
    final answer = await _peerConnection?.createAnswer();
    await _peerConnection?.setLocalDescription(answer);
    
    // Send answer back to server
    // Implementation depends on signaling server
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
                child: _cameraController != null && _cameraController!.value.isInitialized
                  ? CameraPreview(_cameraController!)
                  : Center(child: CircularProgressIndicator()),
              ),
              // Reference video
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
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _feedbackMessage,
                    style: TextStyle(color: Colors.white, fontSize: 18),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Similarity: ${(_similarityScore * 100).toStringAsFixed(1)}%',
                    style: TextStyle(color: Colors.white, fontSize: 14),
                  ),
                  SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: _holdProgress,
                    backgroundColor: Colors.grey,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.green),
                  ),
                  Text(
                    'Hold Progress: ${(_holdProgress * 100).toStringAsFixed(0)}%',
                    style: TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
          
          // Completion overlay
          if (_isCompleted)
            Container(
              color: Colors.black.withOpacity(0.8),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.check_circle, color: Colors.green, size: 80),
                    SizedBox(height: 16),
                    Text(
                      'Exercise Completed!',
                      style: TextStyle(color: Colors.white, fontSize: 24),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
  
  void _showCompletionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Congratulations!'),
        content: Text('You have successfully completed this exercise.'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              Navigator.of(context).pop(); // Go back to task list
            },
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
  
  @override
  void dispose() {
    _cameraController?.dispose();
    _referenceController?.dispose();
    _feedbackChannel?.sink.close();
    _peerConnection?.close();
    super.dispose();
  }
}
```

### 5.2 WebRTC Integration
```dart
// Add to pubspec.yaml
dependencies:
  flutter_webrtc: ^0.9.36
  web_socket_channel: ^2.4.0
  video_player: ^2.7.1
  camera: ^0.10.5
```

## 6. Backend Implementation Steps

### Phase 1: WebRTC Setup
1. Implement WebRTC signaling server
2. Setup STUN/TURN servers cho NAT traversal
3. Handle video stream reception

### Phase 2: Real-time Processing
1. Decode incoming WebRTC frames (30fps)
2. Run pose detection trên mỗi frame
3. Stream feedback qua WebSocket

### Phase 3: Reference Video Management
1. Pre-load reference videos
2. Extract pose sequences từ reference videos
3. Cache pose data để performance

### Phase 4: Session Management
1. Track active sessions
2. Handle session lifecycle (start/end)
3. Cleanup resources

## 7. Performance Optimization

### 7.1 Frame Processing
- **Frame Rate**: 30fps input, process every frame
- **Resolution**: 640x480 đủ cho pose detection
- **Compression**: H.264 cho WebRTC transport

### 7.2 Backend Scaling
- **Async Processing**: Use asyncio cho concurrent sessions
- **GPU Acceleration**: MediaPipe hỗ trợ GPU
- **Horizontal Scaling**: Multiple worker instances

### 7.3 Mobile Optimization
- **Battery**: Optimize camera settings
- **Network**: WebRTC adaptive bitrate
- **UI**: Smooth 30fps updates

## 8. Error Handling & Recovery

### 8.1 Connection Issues
- **WebRTC Disconnect**: Auto-reconnect với exponential backoff
- **WebSocket Disconnect**: Re-establish connection
- **Network Timeout**: Graceful degradation

### 8.2 Processing Errors
- **Pose Detection Fail**: Fallback to basic feedback
- **Reference Video Error**: Use cached pose data
- **Memory Issues**: Limit concurrent sessions per instance

## 9. Testing Strategy

### 9.1 Unit Tests
- Pose detection accuracy
- Feedback generation logic
- Hold timer functionality

### 9.2 Integration Tests
- WebRTC streaming
- WebSocket messaging
- Task completion flow

### 9.3 Performance Tests
- Concurrent users (50+ sessions)
- Frame processing latency
- Memory usage monitoring

---

**Tác giả**: AI Assistant  
**Ngày**: January 13, 2026  
**Version**: 2.0 (Real-time Streaming)</content>
<parameter name="filePath">d:\Innovation\Memotion\POSE_DETECTION_INTEGRATION_STRATEGY.md