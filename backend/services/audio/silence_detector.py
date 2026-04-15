import numpy as np
import librosa
import logging
from typing import Tuple, List
from core.config import settings

logger = logging.getLogger(__name__)


class SilenceDetector:
    def __init__(self):
        self.sample_rate = settings.AUDIO_SAMPLE_RATE
        self.silence_threshold = 0.01  # RMS threshold for silence
        self.min_silence_duration = 0.1  # Minimum silence duration in seconds
    
    def is_silent(self, audio_chunk: np.ndarray) -> bool:
        try:
            if len(audio_chunk) == 0:
                return True
            
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            return bool(rms < self.silence_threshold)
        
        except Exception as e:
            logger.error(f"Silence detection failed: {e}")
            return True  # Default to silent on error
    
    def get_volume_level(self, audio_chunk: np.ndarray) -> float:
        try:
            if len(audio_chunk) == 0:
                return 0.0
            
            # Calculate RMS energy and normalize to 0-1
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            normalized_rms = min(rms * 10, 1.0)  # Scale and cap at 1.0
            return float(normalized_rms)
        
        except Exception as e:
            logger.error(f"Volume calculation failed: {e}")
            return 0.0
    
    def detect_silence_ratio(self, audio_data: np.ndarray) -> float:
        try:
            if len(audio_data) == 0:
                return 1.0
            
            # Calculate RMS for the entire audio
            rms = librosa.feature.rms(y=audio_data)[0]
            
            # Count silent frames
            silent_frames = np.sum(rms < self.silence_threshold)
            total_frames = len(rms)
            
            silence_ratio = silent_frames / total_frames if total_frames > 0 else 1.0
            return float(silence_ratio)
        
        except Exception as e:
            logger.error(f"Silence ratio calculation failed: {e}")
            return 1.0
    
    def get_speaking_segments(self, audio_data: np.ndarray) -> List[Tuple[float, float]]:
        try:
            if len(audio_data) == 0:
                return []
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=audio_data)[0]
            
            # Convert frame indices to time
            frame_times = librosa.frames_to_time(
                np.arange(len(rms)), 
                sr=self.sample_rate
            )
            
            # Find speaking segments
            speaking_segments = []
            is_speaking = False
            start_time = 0
            
            for i, (time, energy) in enumerate(zip(frame_times, rms)):
                if energy >= self.silence_threshold and not is_speaking:
                    is_speaking = True
                    start_time = time
                elif energy < self.silence_threshold and is_speaking:
                    is_speaking = False
                    end_time = time
                    duration = end_time - start_time
                    
                    # Only include segments longer than minimum duration
                    if duration >= self.min_silence_duration:
                        speaking_segments.append((start_time, end_time))
            
            # Handle case where audio ends while speaking
            if is_speaking:
                end_time = frame_times[-1]
                duration = end_time - start_time
                if duration >= self.min_silence_duration:
                    speaking_segments.append((start_time, end_time))
            
            return speaking_segments
        
        except Exception as e:
            logger.error(f"Speaking segment detection failed: {e}")
            return []


# Global instance
silence_detector = SilenceDetector()
