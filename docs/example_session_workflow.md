# Example Session Workflow

This document demonstrates a complete practice session workflow from start to finish.

## 1. User Authentication

```typescript
// Frontend: Firebase Google Sign-In
const { idToken } = await signInWithGoogle();

// Backend: Token verification and JWT creation
POST /api/v1/auth/login
{
  "id_token": "firebase_id_token_here"
}

Response:
{~
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user_id": 123
}
```

## 2. Session Start

```typescript
// Frontend: Start new session
POST /api/v1/session/start
{
  "goal": "reduce_fillers",
  "context": "Practice session for presentation skills"
}

Response:
{
  "id": 456,
  "user_id": 123,
  "goal": "reduce_fillers",
  "context": "Practice session for presentation skills",
  "start_time": "2024-03-12T10:30:00Z",
  "end_time": null
}
```

## 3. WebSocket Connection

```typescript
// Frontend: Establish WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/v1/session/ws/456');

// Real-time audio streaming
ws.send(JSON.stringify({
  type: 'audio_chunk',
  audio_data: 'base64_encoded_audio',
  goal: 'reduce_fillers'
}));
```

## 4. Real-time Feedback

```typescript
// Backend: Real-time analysis response
{
  "type": "realtime_feedback",
  "metrics": {
    "wpm": 145.2,
    "filler_count": 2,
    "filler_ratio": 0.035,
    "silence_detected": false,
    "volume_level": 0.78
  }
}
```

## 5. Session Completion

```typescript
// Frontend: Send complete audio for analysis
ws.send(JSON.stringify({
  type: 'session_complete',
  audio_data: 'base64_encoded_full_audio',
  goal: 'reduce_fillers'
}));

// Backend: Complete analysis response
{
  "type": "analysis_complete",
  "results": {
    "wpm": 142.5,
    "filler_count": 8,
    "filler_ratio": 0.045,
    "avg_pause": 2.3,
    "pitch_variance": 185.7,
    "confidence_score": 0.78,
    "emotion_label": "confident",
    "goal_score": 0.82,
    "transcription": "Hello everyone, today I'd like to talk about...",
    "improvement_suggestions": [
      "Try to reduce filler words - currently at 4.5%",
      "Great speaking pace - keep it up!",
      "Consider adding more vocal variety"
    ]
  }
}
```

## 6. Session End

```typescript
// Frontend: End session
POST /api/v1/session/456/end

Response:
{
  "id": 456,
  "user_id": 123,
  "goal": "reduce_fillers",
  "context": "Practice session for presentation skills",
  "start_time": "2024-03-12T10:30:00Z",
  "end_time": "2024-03-12T10:35:00Z",
  "metrics": {
    "session_id": 456,
    "wpm": 142.5,
    "filler_count": 8,
    "filler_ratio": 0.045,
    "avg_pause": 2.3,
    "pitch_variance": 185.7,
    "confidence_score": 0.78,
    "emotion_label": "confident",
    "goal_score": 0.82
  }
}
```

## 7. Analytics Update

```typescript
// Frontend: Get updated analytics
GET /api/v1/dashboard/analytics

Response:
{
  "last_15_sessions": [...],
  "wpm_growth": 15.3,
  "filler_reduction": 32.8,
  "confidence_trend": "improving",
  "insights": [
    "Speaking rate improved by 15%",
    "Filler words reduced by 33%",
    "Confidence significantly improved in recent sessions"
  ]
}
```

## Error Handling Examples

### WebSocket Disconnection
```typescript
// Automatic reconnection logic
ws.onclose = (event) => {
  if (event.code !== 1000) {
    // Attempt reconnection
    setTimeout(() => connectWebSocket(sessionId), 1000);
  }
};
```

### Audio Processing Error
```typescript
// Backend error response
{
  "type": "error",
  "message": "Audio processing failed - please try again"
}
```

### Session Validation Error
```typescript
// Frontend validation
if (!audioData || audioData.length === 0) {
  throw new Error("No audio data available for analysis");
}
```

## Performance Metrics

### Session Statistics
- **Duration**: 5 minutes
- **Audio Size**: 2.3MB
- **Processing Time**: 1.2 seconds
- **Real-time Updates**: 30 feedback messages
- **Accuracy**: 94% transcription accuracy

### User Progress
- **Total Sessions**: 15
- **Practice Hours**: 12.5
- **WPM Improvement**: +15.3%
- **Filler Reduction**: -32.8%
- **Confidence Growth**: +22.5%

This workflow demonstrates the complete user journey from authentication through practice session completion and analytics updates.
