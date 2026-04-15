import whisper
import numpy as np
import io
import logging
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self):
        try:
            self.model = whisper.load_model(settings.WHISPER_MODEL)
            logger.info(f"Whisper model '{settings.WHISPER_MODEL}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        if self.model is None:
            logger.error("Whisper model not available")
            return None
        
        try:
            # Resample if necessary
            if sample_rate != 16000:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
            
            # Transcribe
            result = self.model.transcribe(audio_data, fp16=False)
            return result.get("text", "").strip()
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def transcribe_audio_file(self, audio_file: bytes) -> Optional[str]:
        if self.model is None:
            return None
        
        try:
            # Load audio from bytes
            import io
            import soundfile as sf
            
            audio_data, sample_rate = sf.read(io.BytesIO(audio_file))
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            return self.transcribe_audio(audio_data, sample_rate)
        
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            return None


# Global instance
whisper_service = WhisperService()
