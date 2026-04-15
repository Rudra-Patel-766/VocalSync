from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SessionTrend(BaseModel):
    session_id: int
    date: datetime
    wpm: float
    filler_ratio: float
    confidence_score: float


class AnalyticsResponse(BaseModel):
    last_15_sessions: List[SessionTrend]
    wpm_growth: float  # percentage change
    filler_reduction: float  # percentage change
    confidence_trend: str  # "improving", "stable", "declining"
    insights: List[str]
    
    class Config:
        from_attributes = True


class SkillComparison(BaseModel):
    skill: str
    current_value: float
    average_value: float
    improvement: float


class DashboardAnalytics(BaseModel):
    trend_data: AnalyticsResponse
    skill_comparison: List[SkillComparison]
    total_sessions: int
    practice_hours: float
