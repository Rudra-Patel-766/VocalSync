import asyncio
import logging
import numpy as np
import time
from typing import Dict, Any, Optional
from services.speech.whisper_service import whisper_service
from services.speech.filler_detector import filler_detector
from services.audio.feature_extractor import audio_feature_extractor
from services.audio.silence_detector import silence_detector
from services.emotion.emotion_analyzer import emotion_analyzer
from services.scoring.goal_scorer import goal_scorer
from models.session import GoalType


def convert_numpy_to_python(obj: Any) -> Any:
    """
    Recursively convert numpy and other non-JSON-serializable types to native Python types.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_to_python(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj) if isinstance(obj, np.floating) else int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj

logger = logging.getLogger(__name__)


def convert_metrics_to_feedback(metrics: dict) -> dict:
    """
    Convert raw metrics to user-friendly feedback messages.
    Always returns feedback dict with available messages.
    """
    feedback = {}
    
    # Speaking pace feedback
    if 'wpm' in metrics and metrics['wpm'] > 0:
        wpm = metrics['wpm']
        if wpm < 100:
            feedback['pace_feedback'] = "Speaking too slow - try to speak a bit faster"
        elif wpm > 160:
            feedback['pace_feedback'] = "Speaking too fast - try to slow down"
        else:
            feedback['pace_feedback'] = "Good speaking pace"
    
    # Volume feedback
    if 'volume_level' in metrics:
        volume = metrics['volume_level']
        if volume < 0.3:
            feedback['volume_feedback'] = "Speak up - increase your voice volume"
        elif volume > 0.9:
            feedback['volume_feedback'] = "Volume is good"
        else:
            feedback['volume_feedback'] = "Volume is good"
    
    # Silence detection feedback
    if 'silence_detected' in metrics:
        if metrics['silence_detected']:
            feedback['silence_feedback'] = "Silence detected - keep speaking"
        else:
            feedback['silence_feedback'] = "Good - keep speaking"
    
    # Filler words feedback
    if 'filler_ratio' in metrics and metrics['filler_ratio'] > 0:
        filler_ratio = metrics['filler_ratio']
        if filler_ratio > 0.1:
            feedback['filler_feedback'] = "Too many filler words - try pausing instead"
        elif filler_ratio > 0.05:
            feedback['filler_feedback'] = "Reduce filler words"
        else:
            feedback['filler_feedback'] = "Good - minimal filler words"
    
    return feedback


class AnalysisWorker:
    def __init__(self):
        self.session_buffers: Dict[int, list[np.ndarray]] = {}
        self.session_start_time = None
        self.total_audio_duration = 0
        self.session_realtime_metrics: Dict[int, Dict[str, float]] = {}
        self.session_chunk_count: Dict[int, int] = {}
        self.session_last_realtime_analysis_at: Dict[int, float] = {}
        self.realtime_analysis_chunk_interval = 12
        self.realtime_analysis_min_seconds = 3.0
    
    async def process_audio_chunk(self, audio_chunk: np.ndarray, session_goal: GoalType, session_id: int) -> Dict[str, Any]:
        """
        Process a single audio chunk for real-time feedback
        """
        try:
            session_buffer = self.session_buffers.setdefault(session_id, [])
            session_metrics = self.session_realtime_metrics.setdefault(session_id, {
                'wpm': 0.0,
                'filler_count': 0,
                'filler_ratio': 0.0
            })
            chunk_count = self.session_chunk_count.get(session_id, 0) + 1
            self.session_chunk_count[session_id] = chunk_count

            # Always include baseline real-time metrics so frontend widgets do not appear empty.
            realtime_metrics = dict(session_metrics)
            
            # Volume level
            volume_level = silence_detector.get_volume_level(audio_chunk)
            realtime_metrics['volume_level'] = volume_level
            
            # Silence detection
            is_silent = silence_detector.is_silent(audio_chunk)
            realtime_metrics['silence_detected'] = is_silent
            
            # Add to buffer for later analysis
            session_buffer.append(audio_chunk)
            
            # Throttle expensive text analysis so websocket feedback remains responsive.
            now = time.time()
            last_realtime_analysis_at = self.session_last_realtime_analysis_at.get(session_id, 0.0)
            is_analysis_interval = chunk_count % self.realtime_analysis_chunk_interval == 0
            passed_min_window = (now - last_realtime_analysis_at) >= self.realtime_analysis_min_seconds

            if len(session_buffer) >= self.realtime_analysis_chunk_interval and is_analysis_interval and passed_min_window:
                self.session_last_realtime_analysis_at[session_id] = now
                cumulative_metrics = await self._calculate_cumulative_metrics(session_buffer[-48:], session_goal)
                realtime_metrics.update(cumulative_metrics)
                session_metrics.update(cumulative_metrics)
            
            # Convert raw metrics to user-friendly feedback
            feedback = convert_metrics_to_feedback(realtime_metrics)
            
            return convert_numpy_to_python(feedback)
        
        except Exception as e:
            logger.error(f"Audio chunk processing failed: {e}")
            return {}
    
    async def _calculate_cumulative_metrics(self, audio_chunks: list[np.ndarray], session_goal: GoalType) -> Dict[str, Any]:
        """
        Calculate metrics from accumulated audio buffer
        """
        try:
            if not audio_chunks:
                return {}
            
            # Concatenate audio chunks
            combined_audio = np.concatenate(audio_chunks)
            
            # Transcribe recent audio
            transcription = whisper_service.transcribe_audio(combined_audio)
            
            if not transcription:
                return {}
            
            metrics = {}
            
            # Calculate speaking rate
            duration_seconds = len(combined_audio) / 16000  # Assuming 16kHz sample rate
            wpm = audio_feature_extractor.calculate_speaking_rate(transcription, duration_seconds)
            metrics['wpm'] = wpm
            
            # Analyze filler words
            filler_count, filler_ratio = filler_detector.calculate_filler_ratio(transcription)
            metrics['filler_count'] = filler_count
            metrics['filler_ratio'] = filler_ratio
            
            return metrics
        
        except Exception as e:
            logger.error(f"Cumulative metrics calculation failed: {e}")
            return {}
    
    async def analyze_complete_session(self, audio_data: Optional[np.ndarray], session_goal: GoalType, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Perform complete analysis of a session
        """
        try:
            logger.info(f"Starting complete session analysis for session {session_id}")

            if audio_data is None or len(audio_data) == 0:
                buffered_audio = self.get_buffered_audio(session_id)
                if buffered_audio is None or len(buffered_audio) == 0:
                    logger.error("No audio data available for complete analysis")
                    return None
                audio_data = buffered_audio
            
            # Transcribe audio
            transcription = whisper_service.transcribe_audio(audio_data)
            
            if not transcription:
                logger.error("Transcription failed")
                return None
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            
            # Calculate basic metrics
            duration_seconds = len(audio_data) / 16000  # Assuming 16kHz sample rate
            
            # Speaking rate
            wpm = audio_feature_extractor.calculate_speaking_rate(transcription, duration_seconds)
            
            # Filler word analysis
            filler_count, filler_ratio = filler_detector.calculate_filler_ratio(transcription)
            
            # Audio feature extraction
            audio_features = audio_feature_extractor.extract_features(audio_data)
            
            # Silence analysis
            silence_segments, avg_pause = audio_feature_extractor.detect_silence_segments(audio_data)
            pause_ratio = sum(silence_segments) / duration_seconds if duration_seconds > 0 else 0
            
            # Emotion analysis is centralized in the analyzer with model-first fallback behavior.
            emotion_result = emotion_analyzer.get_emotion_result(transcription)
            primary_emotion = emotion_result.get('label', 'neutral')
            emotion_scores = emotion_result.get('scores', {'neutral': 1.0})
            emotion_source = emotion_result.get('source', 'rule_based')
            
            # Calculate confidence score
            metrics_dict = {
                'wpm': wpm,
                'filler_ratio': filler_ratio,
                'pause_ratio': pause_ratio,
                'pitch_variance': audio_features.get('pitch_variance', 0)
            }
            
            confidence_score = goal_scorer.calculate_confidence_score(metrics_dict, session_goal)
            goal_score = goal_scorer.calculate_goal_score(metrics_dict, session_goal)
            
            # Compile final metrics
            final_metrics = {
                'wpm': wpm,
                'filler_count': filler_count,
                'filler_ratio': filler_ratio,
                'avg_pause': avg_pause,
                'pause_ratio': pause_ratio,
                'pitch_variance': audio_features.get('pitch_variance', 0),
                'confidence_score': confidence_score,
                'emotion_label': primary_emotion,
                'emotion_source': emotion_source,
                'goal_score': goal_score,
                'transcription': transcription,
                'duration': duration_seconds,
                'audio_features': audio_features,
                'emotion_scores': emotion_scores,
                'filler_breakdown': filler_detector.get_filler_breakdown(transcription),
                'silence_segments': len(silence_segments),
                'score_breakdown': goal_scorer.get_score_breakdown(metrics_dict, session_goal),
                'improvement_suggestions': goal_scorer.get_improvement_suggestions(metrics_dict, session_goal),
                'emotion_suggestions': emotion_analyzer.suggest_improvements(transcription),
                'filler_suggestions': filler_detector.suggest_improvements(transcription)
            }
            
            logger.info("Session analysis completed successfully")
            return convert_numpy_to_python(final_metrics)
        
        except Exception as e:
            logger.error(f"Complete session analysis failed: {e}")
            return None
    
    def reset_session(self, session_id: int):
        """
        Reset worker state for new session
        """
        self.session_buffers[session_id] = []
        self.session_realtime_metrics[session_id] = {
            'wpm': 0.0,
            'filler_count': 0,
            'filler_ratio': 0.0
        }
        self.session_chunk_count[session_id] = 0
        self.session_last_realtime_analysis_at[session_id] = 0.0

    def clear_session(self, session_id: int):
        self.session_buffers.pop(session_id, None)
        self.session_realtime_metrics.pop(session_id, None)
        self.session_chunk_count.pop(session_id, None)
        self.session_last_realtime_analysis_at.pop(session_id, None)

    def get_buffered_audio(self, session_id: int) -> Optional[np.ndarray]:
        session_buffer = self.session_buffers.get(session_id, [])
        if not session_buffer:
            return None
        return np.concatenate(session_buffer)
    
    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """
        Get current session statistics
        """
        session_buffer = self.session_buffers.get(session_id, [])
        return {
            'audio_chunks_processed': len(session_buffer),
            'session_duration': self.total_audio_duration,
            'buffer_size': len(session_buffer)
        }


# Global instance
analysis_worker = AnalysisWorker()
