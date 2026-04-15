from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.session import GoalType


class SessionCreate(BaseModel):
    goal: GoalType
    context: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    user_id: int
    goal: GoalType
    context: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    
    class Config:
        from_attributes = True


class SessionMetrics(BaseModel):
    session_id: int
    wpm: float
    filler_count: int
    filler_ratio: float
    avg_pause: float
    pitch_variance: float
    confidence_score: float
    emotion_label: str
    goal_score: float
    
    class Config:
        from_attributes = True


class SessionWithMetrics(BaseModel):
    id: int
    user_id: int
    goal: GoalType
    context: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    metrics: Optional[SessionMetrics] = None
    
    class Config:
        from_attributes = True


class RealtimeMetrics(BaseModel):
    wpm: Optional[float] = None
    filler_count: Optional[int] = None
    filler_ratio: Optional[float] = None
    silence_detected: Optional[bool] = None
    volume_level: Optional[float] = None
