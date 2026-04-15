import logging
from typing import Dict, Any
from models.session import GoalType

logger = logging.getLogger(__name__)


class GoalScorer:
    def __init__(self):
        # Define scoring weights for different goals
        self.goal_weights = {
            GoalType.REDUCE_FILLERS: {
                'filler_ratio': 0.5,
                'wpm': 0.2,
                'pause_ratio': 0.2,
                'pitch_variance': 0.1
            },
            GoalType.IMPROVE_FLUENCY: {
                'wpm': 0.4,
                'pause_ratio': 0.3,
                'filler_ratio': 0.2,
                'pitch_variance': 0.1
            },
            GoalType.INTERVIEW_PRACTICE: {
                'wpm': 0.3,
                'filler_ratio': 0.3,
                'pause_ratio': 0.2,
                'pitch_variance': 0.2
            },
            GoalType.PRESENTATION_PRACTICE: {
                'pitch_variance': 0.3,
                'wpm': 0.3,
                'pause_ratio': 0.2,
                'filler_ratio': 0.2
            }
        }
        
        # Define optimal ranges for each metric
        self.optimal_ranges = {
            'wpm': {'min': 120, 'max': 160, 'ideal': 140},
            'filler_ratio': {'min': 0, 'max': 0.1, 'ideal': 0.02},
            'pause_ratio': {'min': 0.1, 'max': 0.3, 'ideal': 0.2},
            'pitch_variance': {'min': 50, 'max': 500, 'ideal': 200}
        }
    
    def calculate_confidence_score(self, metrics: Dict[str, float], goal: GoalType) -> float:
        try:
            weights = self.goal_weights.get(goal, self.goal_weights[GoalType.IMPROVE_FLUENCY])
            
            # Normalize each metric to 0-1 scale
            normalized_metrics = {}
            
            # Normalize WPM (words per minute)
            wpm = metrics.get('wpm', 0)
            normalized_metrics['wpm'] = self._normalize_metric(wpm, 'wpm')
            
            # Normalize filler ratio (lower is better)
            filler_ratio = metrics.get('filler_ratio', 1.0)
            normalized_metrics['filler_ratio'] = 1.0 - self._normalize_metric(filler_ratio, 'filler_ratio')
            
            # Normalize pause ratio
            pause_ratio = metrics.get('pause_ratio', 0.5)
            normalized_metrics['pause_ratio'] = self._normalize_metric(pause_ratio, 'pause_ratio')
            
            # Normalize pitch variance
            pitch_variance = metrics.get('pitch_variance', 0)
            normalized_metrics['pitch_variance'] = self._normalize_metric(pitch_variance, 'pitch_variance')
            
            # Calculate weighted score
            confidence_score = 0.0
            for metric, weight in weights.items():
                confidence_score += normalized_metrics.get(metric, 0) * weight
            
            # Ensure score is between 0 and 1
            confidence_score = max(0.0, min(1.0, confidence_score))
            
            return float(confidence_score)
        
        except Exception as e:
            logger.error(f"Confidence score calculation failed: {e}")
            return 0.5  # Return neutral score on error
    
    def _normalize_metric(self, value: float, metric_name: str) -> float:
        try:
            optimal = self.optimal_ranges[metric_name]
            min_val = optimal['min']
            max_val = optimal['max']
            ideal = optimal['ideal']
            
            # If value is outside range, normalize to 0
            if value < min_val or value > max_val:
                return 0.0
            
            # Calculate distance from ideal
            if value <= ideal:
                # Value is below ideal, normalize based on distance from min to ideal
                normalized = (value - min_val) / (ideal - min_val)
            else:
                # Value is above ideal, normalize based on distance from ideal to max
                normalized = 1.0 - ((value - ideal) / (max_val - ideal))
            
            return max(0.0, min(1.0, normalized))
        
        except Exception as e:
            logger.error(f"Metric normalization failed for {metric_name}: {e}")
            return 0.5
    
    def calculate_goal_score(self, metrics: Dict[str, float], goal: GoalType) -> float:
        confidence_score = self.calculate_confidence_score(metrics, goal)
        
        # Apply goal-specific adjustments
        if goal == GoalType.REDUCE_FILLERS:
            # Bonus for very low filler ratio
            filler_ratio = metrics.get('filler_ratio', 1.0)
            if filler_ratio < 0.05:
                confidence_score = min(1.0, confidence_score + 0.1)
        
        elif goal == GoalType.IMPROVE_FLUENCY:
            # Bonus for consistent speaking rate
            wpm = metrics.get('wpm', 0)
            if 130 <= wpm <= 150:
                confidence_score = min(1.0, confidence_score + 0.1)
        
        elif goal == GoalType.INTERVIEW_PRACTICE:
            # Bonus for balanced metrics
            filler_ratio = metrics.get('filler_ratio', 1.0)
            pause_ratio = metrics.get('pause_ratio', 0.5)
            if filler_ratio < 0.08 and 0.15 <= pause_ratio <= 0.25:
                confidence_score = min(1.0, confidence_score + 0.1)
        
        elif goal == GoalType.PRESENTATION_PRACTICE:
            # Bonus for expressive speech
            pitch_variance = metrics.get('pitch_variance', 0)
            if pitch_variance > 150:
                confidence_score = min(1.0, confidence_score + 0.1)
        
        return float(confidence_score)
    
    def get_score_breakdown(self, metrics: Dict[str, float], goal: GoalType) -> Dict[str, Any]:
        weights = self.goal_weights.get(goal, self.goal_weights[GoalType.IMPROVE_FLUENCY])
        
        breakdown = {}
        
        for metric_name, weight in weights.items():
            value = metrics.get(metric_name, 0)
            normalized = self._normalize_metric(value, metric_name)
            weighted_score = normalized * weight
            
            breakdown[metric_name] = {
                'value': value,
                'normalized': normalized,
                'weight': weight,
                'weighted_score': weighted_score,
                'optimal_range': self.optimal_ranges[metric_name]
            }
        
        # Calculate total score
        total_score = sum(item['weighted_score'] for item in breakdown.values())
        
        return {
            'breakdown': breakdown,
            'total_score': total_score,
            'goal': goal.value,
            'grade': self._get_grade(total_score)
        }
    
    def _get_grade(self, score: float) -> str:
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Very Good"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        elif score >= 0.5:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def get_improvement_suggestions(self, metrics: Dict[str, float], goal: GoalType) -> list:
        suggestions = []
        weights = self.goal_weights.get(goal, self.goal_weights[GoalType.IMPROVE_FLUENCY])
        
        # Analyze each metric based on its importance for the goal
        for metric_name, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            value = metrics.get(metric_name, 0)
            optimal = self.optimal_ranges[metric_name]
            
            if metric_name == 'wpm':
                if value < optimal['min']:
                    suggestions.append(f"Try to speak faster - aim for {optimal['ideal']}-{optimal['max']} words per minute")
                elif value > optimal['max']:
                    suggestions.append(f"Slow down your speaking rate to {optimal['min']}-{optimal['max']} words per minute")
            
            elif metric_name == 'filler_ratio':
                if value > optimal['max']:
                    suggestions.append(f"Reduce filler words - currently at {value:.1%}, aim for under {optimal['max']:.1%}")
            
            elif metric_name == 'pause_ratio':
                if value < optimal['min']:
                    suggestions.append("Add more strategic pauses to improve clarity")
                elif value > optimal['max']:
                    suggestions.append("Reduce excessive pauses to maintain flow")
            
            elif metric_name == 'pitch_variance':
                if value < optimal['min']:
                    suggestions.append("Add more vocal variety to make your speech more engaging")
                elif value > optimal['max']:
                    suggestions.append("Your pitch variation is very high - try to be more consistent")
        
        if not suggestions:
            suggestions.append("Great job! Your metrics are well-balanced for your goal.")
        
        return suggestions


# Global instance
goal_scorer = GoalScorer()
