import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FillerDetector:
    def __init__(self):
        self.filler_words = (
            'um', 'uh', 'er', 'ah', 'you know', 'I mean',
            'kind of', 'sort of', 'basically', 'actually', 'literally',
            'maybe', 'probably', 'I guess', 'hmm', 'huh'
        )

        # Compile regex patterns in a stable order so counts map to the right filler.
        self.filler_patterns = [
            (word, re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE))
            for word in self.filler_words
        ]
    
    def detect_fillers(self, text: str) -> Dict[str, int]:
        if not text:
            return {}
        
        filler_counts = {}
        text_lower = text.lower()
        
        for filler_word, pattern in self.filler_patterns:
            matches = pattern.findall(text_lower)
            if matches:
                filler_counts[filler_word] = len(matches)
        
        return filler_counts
    
    def calculate_filler_ratio(self, text: str) -> Tuple[int, float]:
        if not text:
            return 0, 0.0
        
        # Count total words
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return 0, 0.0
        
        # Count filler words
        filler_counts = self.detect_fillers(text)
        filler_count = sum(filler_counts.values())
        
        # Calculate ratio
        filler_ratio = filler_count / total_words
        
        return filler_count, filler_ratio
    
    def get_filler_breakdown(self, text: str) -> List[Dict[str, any]]:
        filler_counts = self.detect_fillers(text)
        
        # Sort by frequency
        sorted_fillers = sorted(
            filler_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"word": word, "count": count, "percentage": (count / sum(filler_counts.values()) * 100) if filler_counts else 0}
            for word, count in sorted_fillers
        ]
    
    def suggest_improvements(self, text: str) -> List[str]:
        filler_counts = self.detect_fillers(text)
        
        if not filler_counts:
            return ["Great job! No filler words detected."]
        
        suggestions = []
        
        # Find most common fillers
        most_common = max(filler_counts.items(), key=lambda x: x[1])
        suggestions.append(f"Your most common filler word is '{most_common[0]}' ({most_common[1]} times)")
        
        # General suggestions
        total_fillers = sum(filler_counts.values())
        if total_fillers > 10:
            suggestions.append("Try to pause briefly instead of using filler words")
        elif total_fillers > 5:
            suggestions.append("Practice speaking more slowly to reduce fillers")
        
        suggestions.append("Consider recording yourself and practicing replacement phrases")
        
        return suggestions


# Global instance
filler_detector = FillerDetector()
