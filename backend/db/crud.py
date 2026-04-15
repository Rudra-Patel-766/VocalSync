from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload
from models.user import User
from models.session import Session as SessionModel, GoalType
from models.metrics import SessionMetrics
from schemas.session import SessionCreate, SessionMetrics as SessionMetricsSchema
from typing import List, Optional


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()


def create_user(db: Session, firebase_uid: str, email: str) -> User:
    db_user = User(firebase_uid=firebase_uid, email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_session(db: Session, session_data: SessionCreate, user_id: int) -> SessionModel:
    db_session = SessionModel(
        user_id=user_id,
        goal=session_data.goal,
        context=session_data.context
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def end_session(db: Session, session_id: int) -> SessionModel:
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if db_session:
        db_session.end_time = func.now()
        db.commit()
        db.refresh(db_session)
    return db_session


def create_session_metrics(db: Session, metrics) -> SessionMetrics:
    """
    Create session metrics. Accepts both dict and schema objects.
    """
    session_id = metrics['session_id'] if isinstance(metrics, dict) else metrics.session_id
    existing_metrics = db.query(SessionMetrics).filter(SessionMetrics.session_id == session_id).first()

    if existing_metrics:
        if isinstance(metrics, dict):
            existing_metrics.wpm = metrics.get('wpm', existing_metrics.wpm)
            existing_metrics.filler_count = metrics.get('filler_count', existing_metrics.filler_count)
            existing_metrics.filler_ratio = metrics.get('filler_ratio', existing_metrics.filler_ratio)
            existing_metrics.avg_pause = metrics.get('avg_pause', existing_metrics.avg_pause)
            existing_metrics.pitch_variance = metrics.get('pitch_variance', existing_metrics.pitch_variance)
            existing_metrics.confidence_score = metrics.get('confidence_score', existing_metrics.confidence_score)
            existing_metrics.emotion_label = metrics.get('emotion_label', existing_metrics.emotion_label)
            existing_metrics.goal_score = metrics.get('goal_score', existing_metrics.goal_score)
        else:
            existing_metrics.wpm = metrics.wpm
            existing_metrics.filler_count = metrics.filler_count
            existing_metrics.filler_ratio = metrics.filler_ratio
            existing_metrics.avg_pause = metrics.avg_pause
            existing_metrics.pitch_variance = metrics.pitch_variance
            existing_metrics.confidence_score = metrics.confidence_score
            existing_metrics.emotion_label = metrics.emotion_label
            existing_metrics.goal_score = metrics.goal_score

        db.commit()
        db.refresh(existing_metrics)
        return existing_metrics

    if isinstance(metrics, dict):
        db_metrics = SessionMetrics(
            session_id=metrics['session_id'],
            wpm=metrics.get('wpm', 0),
            filler_count=metrics.get('filler_count', 0),
            filler_ratio=metrics.get('filler_ratio', 0),
            avg_pause=metrics.get('avg_pause', 0),
            pitch_variance=metrics.get('pitch_variance', 0),
            confidence_score=metrics.get('confidence_score', 0),
            emotion_label=metrics.get('emotion_label', 'neutral'),
            goal_score=metrics.get('goal_score', 0)
        )
    else:
        db_metrics = SessionMetrics(
            session_id=metrics.session_id,
            wpm=metrics.wpm,
            filler_count=metrics.filler_count,
            filler_ratio=metrics.filler_ratio,
            avg_pause=metrics.avg_pause,
            pitch_variance=metrics.pitch_variance,
            confidence_score=metrics.confidence_score,
            emotion_label=metrics.emotion_label,
            goal_score=metrics.goal_score
        )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def get_user_sessions(db: Session, user_id: int, limit: int = 50) -> List[SessionModel]:
    return db.query(SessionModel).options(
        joinedload(SessionModel.metrics)
    ).filter(
        SessionModel.user_id == user_id
    ).order_by(desc(SessionModel.start_time)).limit(limit).all()


def get_session_with_metrics(db: Session, session_id: int, user_id: int = None) -> Optional[SessionModel]:
    """
    Get session with metrics. If user_id is provided, filters by it; otherwise returns any session with that ID.
    """
    if user_id is not None:
        return db.query(SessionModel).options(
            joinedload(SessionModel.metrics)
        ).filter(
            SessionModel.id == session_id,
            SessionModel.user_id == user_id
        ).first()
    else:
        return db.query(SessionModel).options(
            joinedload(SessionModel.metrics)
        ).filter(
            SessionModel.id == session_id
        ).first()


def get_last_15_sessions_with_metrics(db: Session, user_id: int) -> List[SessionModel]:
    return db.query(SessionModel).options(
        joinedload(SessionModel.metrics)
    ).join(SessionMetrics).filter(
        SessionModel.user_id == user_id
    ).order_by(desc(SessionModel.start_time)).limit(15).all()


def get_session_count(db: Session, user_id: int) -> int:
    return db.query(SessionModel).filter(SessionModel.user_id == user_id).count()
