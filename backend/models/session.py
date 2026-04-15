from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class GoalType(enum.Enum):
    REDUCE_FILLERS = "reduce_fillers"
    IMPROVE_FLUENCY = "improve_fluency"
    INTERVIEW_PRACTICE = "interview_practice"
    PRESENTATION_PRACTICE = "presentation_practice"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal = Column(
        Enum(
            GoalType,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    context = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    metrics = relationship("SessionMetrics", back_populates="session", uselist=False)


# Update User model to include back_populates
from models.user import User
User.sessions = relationship("Session", back_populates="user")
