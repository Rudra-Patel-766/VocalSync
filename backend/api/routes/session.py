from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import json
import asyncio
import numpy as np
import base64
import io
import logging

from db.database import get_db, SessionLocal
from db.crud import (
    create_session, end_session, get_user_sessions, 
    get_session_with_metrics, create_session_metrics
)
from api.routes.auth import get_current_user
from schemas.session import SessionCreate, SessionResponse, SessionWithMetrics, RealtimeMetrics
from models.session import GoalType
from workers.analysis_worker import analysis_worker
from services.recommendation_service import generate_session_recommendations

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[int, WebSocket] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                message_json = json.dumps(message)
                logger.debug(
                    f"Sending message to user {user_id}: {message.get('type', 'unknown')}"
                )
                await self.active_connections[user_id].send_text(message_json)
            except Exception as e:
                error_type = type(e).__name__
                logger.warning(
                    f"Failed to send message to user {user_id} ({error_type}): {str(e)}"
                )
                # Remove broken connection
                self.disconnect(user_id)


manager = ConnectionManager()

# In-memory cache for session recommendations (maps session_id -> recommendations)
recommendations_cache: Dict[int, dict] = {}


async def generate_recommendations_background(user_id: int, session_id: int, goal_value: str, analysis_result: dict):
    """
    Generate AI recommendations in background without blocking.
    Stores results in cache for polling via REST endpoint.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting background recommendation generation for session {session_id}")
        
        previous_sessions = get_user_sessions(db, user_id, limit=10)
        ai_result = generate_session_recommendations(
            metrics=analysis_result,
            goal=goal_value,
            previous_sessions=previous_sessions,
        )
        
        analysis_result["ai_recommendations"] = ai_result["recommendations"]
        analysis_result["ai_source"] = ai_result["source"]
        logger.info(f"AI recommendations generated via {ai_result['source']} for session {session_id}")
        
        # Store in cache for REST polling
        recommendations_cache[session_id] = {
            "status": "ready",
            "recommendations": ai_result["recommendations"],
            "source": ai_result["source"]
        }
        
    except Exception as e:
        logger.error(f"Recommendation generation failed for session {session_id}: {e}")
        # Store failure status in cache
        recommendations_cache[session_id] = {
            "status": "failed",
            "error": str(e),
            "recommendations": None
        }
    finally:
        db.close()


async def run_background_session_analysis(session_id: int, goal_value: str):
    db = SessionLocal()
    try:
        try:
            goal = GoalType(goal_value)
        except ValueError:
            goal = GoalType.IMPROVE_FLUENCY

        analysis_result = await analysis_worker.analyze_complete_session(None, goal, session_id)
        if not analysis_result:
            logger.warning(f"Background analysis produced no result for session {session_id}")
            return

        # Get user_id for WebSocket messaging
        db_session = get_session_with_metrics(db, session_id, None)
        if not db_session:
            logger.error(f"Session {session_id} not found")
            return
        
        user_id = db_session.user_id

        metrics_schema = {
            'session_id': session_id,
            'wpm': float(analysis_result.get('wpm', 0)),
            'filler_count': int(analysis_result.get('filler_count', 0)),
            'filler_ratio': float(analysis_result.get('filler_ratio', 0)),
            'avg_pause': float(analysis_result.get('avg_pause', 0)),
            'pitch_variance': float(analysis_result.get('pitch_variance', 0)),
            'confidence_score': float(analysis_result.get('confidence_score', 0)),
            'emotion_label': analysis_result.get('emotion_label', 'neutral'),
            'goal_score': float(analysis_result.get('goal_score', 0))
        }
        create_session_metrics(db, metrics_schema)
        
        # Send initial analysis results to frontend immediately
        await manager.send_personal_message({
            "type": "analysis_complete",
            "results": analysis_result,
        }, user_id)
        
        # Spawn recommendation generation as NON-BLOCKING background task
        asyncio.create_task(generate_recommendations_background(
            user_id=user_id,
            session_id=session_id,
            goal_value=goal_value,
            analysis_result=analysis_result
        ))
        
        analysis_worker.clear_session(session_id)
        logger.info(f"Background metrics saved for session {session_id}")
        
    except Exception as e:
        logger.error(f"Background analysis failed for session {session_id}: {e}")
    finally:
        db.close()


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Create new session
        session = create_session(db, session_data, current_user.id)
        
        # Reset analysis worker
        analysis_worker.reset_session(session.id)
        
        logger.info(f"Session {session.id} started for user {current_user.id}")
        
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            goal=session.goal,
            context=session.context,
            start_time=session.start_time,
            end_time=session.end_time
        )
    
    except Exception as e:
        logger.error(f"Session start failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/{session_id}/end", response_model=SessionWithMetrics)
async def end_session_endpoint(
    session_id: int,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get session
        session = get_session_with_metrics(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        # End session
        end_session(db, session_id)

        # Trigger full analysis in the background using buffered session audio.
        goal_value = session.goal.value if hasattr(session.goal, "value") else str(session.goal)
        background_tasks.add_task(run_background_session_analysis, session_id, goal_value)
        
        # For now, return session without metrics (will be updated when audio is processed)
        return SessionWithMetrics(
            id=session.id,
            user_id=session.user_id,
            goal=session.goal,
            context=session.context,
            start_time=session.start_time,
            end_time=session.end_time,
            metrics=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session end failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end session: {str(e)}"
        )


@router.get("/", response_model=List[SessionWithMetrics])
async def get_user_sessions_endpoint(
    limit: int = 50,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        sessions = get_user_sessions(db, current_user.id, limit)
        
        result = []
        for session in sessions:
            session_data = SessionWithMetrics(
                id=session.id,
                user_id=session.user_id,
                goal=session.goal,
                context=session.context,
                start_time=session.start_time,
                end_time=session.end_time,
                metrics=session.metrics if session.metrics else None
            )
            result.append(session_data)
        
        return result
    
    except Exception as e:
        logger.error(f"Get sessions failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionWithMetrics)
async def get_session_endpoint(
    session_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        session = get_session_with_metrics(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return SessionWithMetrics(
            id=session.id,
            user_id=session.user_id,
            goal=session.goal,
            context=session.context,
            start_time=session.start_time,
            end_time=session.end_time,
            metrics=session.metrics if session.metrics else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/{session_id}/recommendations")
async def get_recommendations(
    session_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Poll for AI recommendations after session ends.
    Returns: {"status": "pending|ready|failed", "recommendations": str or None}
    """
    try:
        # Verify user owns this session
        session = get_session_with_metrics(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        # Check cache for recommendations
        if session_id in recommendations_cache:
            cached = recommendations_cache[session_id]
            return {
                "status": cached["status"],
                "recommendations": cached.get("recommendations"),
                "source": cached.get("source"),
                "error": cached.get("error")
            }
        
        # Not ready yet
        return {
            "status": "pending",
            "recommendations": None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time audio streaming and feedback
    """
    # Get user_id from session
    db_session = get_session_with_metrics(db, session_id, None)
    if not db_session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    user_id = db_session.user_id
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "audio_chunk":
                # Process audio chunk
                await handle_audio_chunk(message, session_id)
            
            elif message_type == "session_complete":
                # Handle session completion
                await handle_session_complete(message, session_id, user_id, db)
            
            elif message_type == "ping":
                # Handle ping/pong for connection health
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


async def handle_audio_chunk(message: dict, session_id: int):
    """
    Handle incoming audio chunk and provide real-time feedback
    """
    try:
        # Extract audio data
        audio_data_b64 = message.get("audio_data")
        goal_str = message.get("goal", "improve_fluency")
        
        if not audio_data_b64:
            return
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_data_b64)
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32).copy()
        
        # Convert goal string to enum
        try:
            goal = GoalType(goal_str)
        except ValueError:
            goal = GoalType.IMPROVE_FLUENCY
        
        # Process audio chunk
        realtime_metrics = await analysis_worker.process_audio_chunk(audio_data, goal, session_id)
        
        # Send feedback to client
        if realtime_metrics:
            await manager.send_personal_message({
                "type": "realtime_feedback",
                "metrics": realtime_metrics
            }, session_id)
    
    except Exception as e:
        logger.error(f"Audio chunk processing failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to process audio chunk"
        }, session_id)


async def handle_session_complete(message: dict, session_id: int, user_id: int, db: Session):
    """
    Handle session completion and perform full analysis
    """
    try:
        # Extract complete audio data
        audio_data_b64 = message.get("audio_data")
        goal_str = message.get("goal", "improve_fluency")
        
        # Prefer payload audio when present, otherwise use server-side buffered audio.
        audio_data = None
        if audio_data_b64:
            try:
                audio_bytes = base64.b64decode(audio_data_b64)
                audio_data = np.frombuffer(audio_bytes, dtype=np.float32).copy()
            except Exception as decode_error:
                logger.warning(f"Failed to decode final audio payload for session {session_id}: {decode_error}")
        
        # Convert goal string to enum
        try:
            goal = GoalType(goal_str)
        except ValueError:
            goal = GoalType.IMPROVE_FLUENCY
        
        # Perform complete analysis
        analysis_result = await analysis_worker.analyze_complete_session(audio_data, goal, session_id)
        
        if analysis_result:
            # Save metrics to database
            try:
                metrics_schema = {
                    'session_id': session_id,
                    'wpm': float(analysis_result.get('wpm', 0)),
                    'filler_count': int(analysis_result.get('filler_count', 0)),
                    'filler_ratio': float(analysis_result.get('filler_ratio', 0)),
                    'avg_pause': float(analysis_result.get('avg_pause', 0)),
                    'pitch_variance': float(analysis_result.get('pitch_variance', 0)),
                    'confidence_score': float(analysis_result.get('confidence_score', 0)),
                    'emotion_label': analysis_result.get('emotion_label', 'neutral'),
                    'goal_score': float(analysis_result.get('goal_score', 0))
                }
                create_session_metrics(db, metrics_schema)
                logger.info(f"Metrics saved for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to save metrics to database: {e}")
            
            # Fetch previous sessions for trend comparison
            try:
                previous_sessions = get_user_sessions(db, user_id, limit=10)
            except Exception:
                previous_sessions = []

            # Generate AI recommendations
            try:
                ai_result = generate_session_recommendations(
                    metrics=analysis_result,
                    goal=goal_str,
                    previous_sessions=previous_sessions,
                )
                analysis_result["ai_recommendations"] = ai_result["recommendations"]
                analysis_result["ai_source"] = ai_result["source"]
            except Exception as e:
                logger.error(f"Recommendation generation failed: {e}")
                analysis_result["ai_recommendations"] = None
                analysis_result["ai_source"] = "error"
            
            # Send analysis results to client
            await manager.send_personal_message({
                "type": "analysis_complete",
                "results": analysis_result
            }, session_id)
            analysis_worker.clear_session(session_id)
            
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Failed to analyze session"
            }, session_id)
    
    except Exception as e:
        logger.error(f"Session completion failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to complete session analysis"
        }, session_id)

