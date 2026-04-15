from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db.database import Base


class SessionMetrics(Base):
    __tablename__ = "session_metrics"

    session_id = Column(Integer, ForeignKey("sessions.id"), primary_key=True)
    wpm = Column(Float, nullable=False)  # Words per minute
    filler_count = Column(Integer, nullable=False)
    filler_ratio = Column(Float, nullable=False)
    avg_pause = Column(Float, nullable=False)  # Average pause duration in seconds
    pitch_variance = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    emotion_label = Column(String(50), nullable=False)
    goal_score = Column(Float, nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="metrics")
