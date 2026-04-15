import re
import logging
from typing import Any, Dict, List
from collections import Counter
from services.emotion.model_emotion_service import model_emotion_service

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    def __init__(self):
        # Rule-based emotion keywords
        self.emotion_keywords = {
            'confident': [
                'absolutely', 'certainly', 'definitely', 'excellent', 'fantastic', 
                'great', 'perfect', 'wonderful', 'amazing', 'outstanding',
                'successful', 'achieve', 'accomplish', 'master', 'expert'
            ],
            'nervous': [
                'maybe', 'perhaps', 'think', 'might', 'could', 'probably',
                'uncertain', 'unsure', 'hesitate', 'worry', 'concern',
                'anxious', 'nervous', 'scared', 'afraid', 'worried'
            ],
            'excited': [
                'excited', 'thrilled', 'enthusiastic', 'passionate', 'energetic',
                'fantastic', 'wonderful', 'amazing', 'incredible', 'awesome',
                'love', 'enjoy', 'happy', 'pleased', 'delighted'
            ],
            'calm': [
                'calm', 'relaxed', 'peaceful', 'serene', 'tranquil',
                'steady', 'balanced', 'composed', 'focused', 'concentrated',
                'clear', 'precise', 'methodical', 'organized'
            ],
            'neutral': [
                # This will be the default if no strong emotion is detected
            ]
        }
        
        # Compile regex patterns for efficient matching
        self.emotion_patterns = {}
        for emotion, keywords in self.emotion_keywords.items():
            self.emotion_patterns[emotion] = [
                re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                for keyword in keywords
            ]
    
    def _analyze_rule_based(self, text: str) -> Dict[str, float]:
        if not text:
            return {'neutral': 1.0}
        
        emotion_scores = {}
        text_lower = text.lower()
        
        # Calculate emotion scores based on keyword matches
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                score += len(matches)
            
            # Normalize by text length
            word_count = len(re.findall(r'\b\w+\b', text))
            if word_count > 0:
                emotion_scores[emotion] = score / word_count
            else:
                emotion_scores[emotion] = 0.0
        
        # If no strong emotion detected, default to neutral
        if all(score < 0.01 for score in emotion_scores.values()):
            emotion_scores['neutral'] = 1.0
        
        return emotion_scores

    def get_emotion_result(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                'label': 'neutral',
                'scores': {'neutral': 1.0},
                'source': 'rule_based'
            }

        model_result = model_emotion_service.predict_emotion(text)
        if model_result:
            model_label = str(model_result.get('label', 'neutral'))
            raw_scores = model_result.get('scores') or {}
            normalized_scores = {
                str(label): float(score)
                for label, score in raw_scores.items()
                if score is not None
            }

            if not normalized_scores:
                normalized_scores = {model_label: 1.0}

            return {
                'label': model_label,
                'scores': normalized_scores,
                'source': model_result.get('source', 'ml_model'),
                'model_version': model_result.get('model_version', 'unknown')
            }

        rule_scores = self._analyze_rule_based(text)
        if not rule_scores:
            return {
                'label': 'neutral',
                'scores': {'neutral': 1.0},
                'source': 'rule_based'
            }

        primary_emotion = max(rule_scores.items(), key=lambda x: x[1])
        label = primary_emotion[0] if primary_emotion[1] >= 0.01 else 'neutral'

        return {
            'label': label,
            'scores': rule_scores,
            'source': 'rule_based'
        }

    def analyze_emotion(self, text: str) -> Dict[str, float]:
        return self.get_emotion_result(text).get('scores', {'neutral': 1.0})
    
    def get_primary_emotion(self, text: str) -> str:
        return str(self.get_emotion_result(text).get('label', 'neutral'))
    
    def get_emotion_breakdown(self, text: str) -> List[Dict[str, any]]:
        emotion_scores = self.analyze_emotion(text)
        
        # Sort by score
        sorted_emotions = sorted(
            emotion_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"emotion": emotion, "score": score, "percentage": score * 100}
            for emotion, score in sorted_emotions if score > 0
        ]
    
    def analyze_emotion_stability(self, text_segments: List[str]) -> Dict[str, any]:
        if not text_segments:
            return {"stability": 0.0, "primary_emotion": "neutral", "emotion_changes": 0}
        
        emotions = []
        for segment in text_segments:
            emotion = self.get_primary_emotion(segment)
            emotions.append(emotion)
        
        # Count emotion changes
        emotion_changes = 0
        for i in range(1, len(emotions)):
            if emotions[i] != emotions[i-1]:
                emotion_changes += 1
        
        # Calculate stability (inverse of changes)
        max_possible_changes = len(emotions) - 1
        stability = 1.0 - (emotion_changes / max_possible_changes) if max_possible_changes > 0 else 1.0
        
        # Get most frequent emotion
        emotion_counts = Counter(emotions)
        primary_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"
        
        return {
            "stability": stability,
            "primary_emotion": primary_emotion,
            "emotion_changes": emotion_changes,
            "emotion_distribution": dict(emotion_counts)
        }
    
    def suggest_improvements(self, text: str) -> List[str]:
        emotion_result = self.get_emotion_result(text)
        primary_emotion = str(emotion_result.get('label', 'neutral'))
        emotion_scores = emotion_result.get('scores', {'neutral': 1.0})
        
        suggestions = []
        
        if primary_emotion == 'nervous':
            suggestions.append("Try using more confident language")
            suggestions.append("Replace uncertain words like 'maybe' with stronger statements")
        elif primary_emotion == 'neutral':
            suggestions.append("Consider adding more enthusiastic language to engage your audience")
            suggestions.append("Use positive and confident words to convey authority")
        elif primary_emotion == 'confident':
            suggestions.append("Great confidence! Maintain this tone throughout")
        elif primary_emotion == 'excited':
            suggestions.append("Good enthusiasm! Balance it with calm, clear explanations")
        
        # Check for emotion variety
        non_zero_emotions = [e for e, s in emotion_scores.items() if s > 0]
        if len(non_zero_emotions) == 1:
            suggestions.append("Try to vary your emotional tone for better engagement")
        
        return suggestions


# Global instance
emotion_analyzer = EmotionAnalyzer()
