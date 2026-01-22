# 🎯 Pose Detection API - Real-time WebSocket

> **Version**: 3.0.0 (Simplified Real-time Only)  
> **Date**: 2026-01-22

## 📋 Tổng Quan

API xử lý **real-time** pose detection thông qua WebSocket. Chỉ có 3 endpoints chính:

```
POST   /api/pose/sessions              → Tạo session, nhận websocket_url
WS     /api/pose/sessions/{id}/ws      → Real-time frame streaming
DELETE /api/pose/sessions/{id}         → Kết thúc, lấy kết quả
```

---

## 🔄 Quy Trình Sử Dụng

```
┌─────────────────────────────────────────────────────────────────┐
│  1. POST /sessions                                               │
│     └── Nhận session_id + websocket_url                         │
│                                                                  │
│  2. Connect WebSocket (sử dụng websocket_url)                    │
│     └── Real-time connection established                        │
│                                                                  │
│  3. Stream Frames (30fps)                                        │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  Client: {"frame_data": "<base64>", "timestamp_ms"} │     │
│     │  Server: {"phase": 1, "data": {...}, "fps": 30}     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
│  4. DELETE /sessions/{id}                                        │
│     └── Nhận final results (scores, recommendations)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

### 1. Health Check

```http
GET /api/pose/health
```

**Response**:
```json
{
  "code": "200",
  "message": "Thành công",
  "data": {
    "status": "healthy",
    "mediapipe_available": true,
    "active_sessions": 3,
    "version": "3.0.0"
  }
}
```

---

### 2. Start Session

```http
POST /api/pose/sessions
Content-Type: application/json

{
  "user_id": "user_123",
  "exercise_type": "arm_raise",
  "default_joint": "left_shoulder"
}
```

**Response**:
```json
{
  "code": "200",
  "message": "Thành công",
  "data": {
    "session_id": "pose_1705900000_1234",
    "status": "active",
    "current_phase": "detection",
    "websocket_url": "/api/pose/sessions/pose_1705900000_1234/ws",
    "message": "Session started. Connect to WebSocket for real-time streaming."
  }
}
```

> ⚠️ **Quan trọng**: Sử dụng `websocket_url` từ response để kết nối WebSocket!

---

### 3. WebSocket Real-time Streaming

```
WS /api/pose/sessions/{session_id}/ws
```

**Client gửi** (30fps):
```json
{
  "frame_data": "/9j/4AAQSkZJRg...",
  "timestamp_ms": 1000
}
```

**Server trả về**:
```json
{
  "phase": 1,
  "phase_name": "detection",
  "data": {
    "pose_detected": true,
    "stable_count": 25,
    "progress": 0.83,
    "landmarks": [...]
  },
  "message": "Đang phát hiện tư thế...",
  "warning": null,
  "timestamp": 1705900800.123,
  "frame_number": 150,
  "fps": 29.8
}
```

**Phase Data**:

| Phase | Data Fields |
|-------|-------------|
| 1. Detection | `pose_detected`, `stable_count`, `progress`, `landmarks` |
| 2. Calibration | `current_joint`, `current_angle`, `max_angle`, `progress` |
| 3. Sync | `video_frame`, `current_score`, `rep_count`, `fatigue_level` |
| 4. Scoring | `total_score`, `rom_score`, `stability_score`, `flow_score`, `grade` |

**Session Completed Event**:
```json
{
  "event": "session_completed",
  "message": "Call DELETE /sessions/{id} for final results."
}
```

---

### 4. End Session

```http
DELETE /api/pose/sessions/{session_id}
```

**Response**:
```json
{
  "code": "200",
  "message": "Thành công",
  "data": {
    "session_id": "pose_1705900000_1234",
    "exercise_name": "Nâng tay",
    "duration_seconds": 300,
    "total_score": 85.5,
    "rom_score": 88.0,
    "stability_score": 82.0,
    "flow_score": 86.0,
    "grade": "XUẤT SẮC",
    "grade_color": "green",
    "total_reps": 10,
    "fatigue_level": "MILD",
    "calibrated_joints": [
      {"joint": "left_shoulder", "max_angle": 165.0}
    ],
    "rep_scores": [
      {"rep": 1, "score": 85.0}
    ],
    "recommendations": [
      "Giữ tốc độ đều",
      "Cố gắng nâng cao hơn 5 độ"
    ]
  }
}
```

---

## 📱 Flutter Integration

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class PoseDetectionService {
  final String baseUrl = 'http://your-server:8000/api/pose';
  String? _sessionId;
  String? _websocketUrl;
  WebSocketChannel? _channel;

  /// 1. Bắt đầu session
  Future<void> startSession({String? userId}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/sessions'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'user_id': userId, 'exercise_type': 'arm_raise'}),
    );

    final data = jsonDecode(response.body)['data'];
    _sessionId = data['session_id'];
    _websocketUrl = data['websocket_url'];
  }

  /// 2. Kết nối WebSocket
  void connectWebSocket() {
    if (_websocketUrl == null) throw Exception('Session not started');
    
    final fullUrl = 'ws://your-server:8000$_websocketUrl';
    _channel = WebSocketChannel.connect(Uri.parse(fullUrl));

    _channel!.stream.listen(
      (message) => _handleResult(jsonDecode(message)),
      onError: (error) => print('WebSocket error: $error'),
    );
  }

  /// 3. Gửi frame (gọi trong camera loop)
  void sendFrame(Uint8List frameBytes, int timestampMs) {
    _channel?.sink.add(jsonEncode({
      'frame_data': base64Encode(frameBytes),
      'timestamp_ms': timestampMs,
    }));
  }

  void _handleResult(Map<String, dynamic> result) {
    if (result.containsKey('event') && result['event'] == 'session_completed') {
      endSession();
      return;
    }

    final phase = result['phase'];
    final data = result['data'];
    
    // Update UI based on phase
    print('Phase $phase: ${result['message']}');
  }

  /// 4. Kết thúc session
  Future<Map<String, dynamic>> endSession() async {
    _channel?.sink.close();
    
    final response = await http.delete(Uri.parse('$baseUrl/sessions/$_sessionId'));
    return jsonDecode(response.body)['data'];
  }
}
```

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| WebSocket Latency | ~10-30ms/frame |
| Recommended FPS | 30 |
| Max Frame Size | 1MB (base64) |
| Session Timeout | 1 hour |

---

## ❌ Error Codes

| Code | Mô tả |
|------|-------|
| 400 | Invalid frame data |
| 404 | Session not found / expired |
| 500 | Internal server error |
| 503 | MediaPipe not available |

---

> **MEMOTION** - Hệ thống chăm sóc sức khỏe cho người cao tuổi
