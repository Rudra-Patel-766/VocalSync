import librosa
import numpy as np
import logging
from typing import Dict, Optional, Tuple
from core.config import settings

logger = logging.getLogger(__name__)


class AudioFeatureExtractor:
    def __init__(self):
        self.sample_rate = settings.AUDIO_SAMPLE_RATE
    
    def extract_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        try:
            features = {}
            
            # Pitch variation (non-critical for real-time)
            try:
                pitch_variance = self._calculate_pitch_variance(audio_data)
                features['pitch_variance'] = pitch_variance
            except Exception as e:
                logger.warning(f"Pitch calculation skipped: {e}")
                features['pitch_variance'] = 0.0
            
            # Speaking rate (will be calculated from text later)
            # Volume statistics (critical)
            try:
                volume_stats = self._calculate_volume_stats(audio_data)
                features.update(volume_stats)
            except Exception as e:
                logger.warning(f"Volume calculation skipped: {e}")
                features.update({'avg_volume': 0.0, 'volume_std': 0.0, 'volume_range': 0.0})
            
            # Energy features (non-critical for real-time)
            try:
                energy_features = self._calculate_energy_features(audio_data)
                features.update(energy_features)
            except Exception as e:
                logger.warning(f"Energy feature calculation skipped: {e}")
                features.update({
                    'avg_spectral_centroid': 0.0,
                    'avg_spectral_rolloff': 0.0,
                    'avg_spectral_bandwidth': 0.0
                })
            
            return features
        
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return safe defaults
            return {
                'pitch_variance': 0.0,
                'avg_volume': 0.0,
                'volume_std': 0.0,
                'volume_range': 0.0,
                'avg_spectral_centroid': 0.0,
                'avg_spectral_rolloff': 0.0,
                'avg_spectral_bandwidth': 0.0
            }
    
    def _calculate_pitch_variance(self, audio_data: np.ndarray) -> float:
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(
                y=audio_data, 
                sr=self.sample_rate,
                threshold=0.1
            )
            
            # Get the pitch values
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Remove unvoiced frames
                    pitch_values.append(pitch)
            
            if len(pitch_values) < 2:
                return 0.0
            
            # Calculate variance
            pitch_variance = np.var(pitch_values)
            return float(pitch_variance)
        
        except Exception as e:
            logger.error(f"Pitch calculation failed: {e}")
            return 0.0
    
    def _calculate_volume_stats(self, audio_data: np.ndarray) -> Dict[str, float]:
        try:
            # RMS energy (volume)
            rms = librosa.feature.rms(y=audio_data)[0]
            
            volume_stats = {
                'avg_volume': float(np.mean(rms)),
                'volume_std': float(np.std(rms)),
                'volume_range': float(np.max(rms) - np.min(rms))
            }
            
            return volume_stats
        
        except Exception as e:
            logger.error(f"Volume calculation failed: {e}")
            return {'avg_volume': 0.0, 'volume_std': 0.0, 'volume_range': 0.0}
    
    def _calculate_energy_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        try:
            # Short-time Fourier transform
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(S=magnitude)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(S=magnitude)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(S=magnitude)[0]
            
            energy_features = {
                'avg_spectral_centroid': float(np.mean(spectral_centroids)),
                'avg_spectral_rolloff': float(np.mean(spectral_rolloff)),
                'avg_spectral_bandwidth': float(np.mean(spectral_bandwidth))
            }
            
            return energy_features
        
        except Exception as e:
            logger.error(f"Energy feature calculation failed: {e}")
            return {
                'avg_spectral_centroid': 0.0,
                'avg_spectral_rolloff': 0.0,
                'avg_spectral_bandwidth': 0.0
            }
    
    def calculate_speaking_rate(self, text: str, duration_seconds: float) -> float:
        if not text or duration_seconds <= 0:
            return 0.0
        
        # Count words
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = len(words)
        
        # Calculate words per minute
        wpm = (word_count / duration_seconds) * 60
        
        return float(wpm)
    
    def detect_silence_segments(self, audio_data: np.ndarray, silence_threshold: float = 0.01) -> Tuple[list, float]:
        try:
            # Calculate RMS energy
            rms = librosa.feature.rms(y=audio_data)[0]
            
            # Detect silence segments
            silence_frames = rms < silence_threshold
            
            # Find silence segments
            silence_segments = []
            in_silence = False
            start_frame = 0
            
            for i, is_silent in enumerate(silence_frames):
                if is_silent and not in_silence:
                    in_silence = True
                    start_frame = i
                elif not is_silent and in_silence:
                    in_silence = False
                    end_frame = i
                    duration = (end_frame - start_frame) / len(rms) * (len(audio_data) / self.sample_rate)
                    silence_segments.append(duration)
            
            # Handle case where audio ends in silence
            if in_silence:
                duration = (len(rms) - start_frame) / len(rms) * (len(audio_data) / self.sample_rate)
                silence_segments.append(duration)
            
            # Calculate average pause duration
            avg_pause = np.mean(silence_segments) if silence_segments else 0.0
            
            return silence_segments, float(avg_pause)
        
        except Exception as e:
            logger.error(f"Silence detection failed: {e}")
            return [], 0.0


# Global instance
audio_feature_extractor = AudioFeatureExtractor()
