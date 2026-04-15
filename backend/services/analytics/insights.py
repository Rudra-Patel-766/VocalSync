import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class InsightsGenerator:
    def __init__(self):
        self.insight_templates = {
            'wpm_improvement': [
                "Your speaking rate has improved by {improvement:.0f}%",
                "Great progress on speaking speed - {improvement:.0f}% faster",
                "Speaking rate improvement: {improvement:.0f}% increase"
            ],
            'wpm_decline': [
                "Speaking rate decreased by {decline:.0f}% - try to maintain pace",
                "Consider practicing to improve speaking speed",
                "Focus on maintaining consistent speaking rate"
            ],
            'filler_reduction': [
                "Excellent! Filler words reduced by {reduction:.0f}%",
                "Great job cutting filler words by {reduction:.0f}%",
                "Filler word improvement: {reduction:.0f}% reduction"
            ],
            'filler_increase': [
                "Filler words increased by {increase:.0f}% - focus on reduction",
                "Try to be more mindful of filler words",
                "Consider practicing with deliberate pauses instead of fillers"
            ],
            'confidence_improvement': [
                "Confidence score is on the rise!",
                "Your confidence has improved significantly",
                "Great progress in building confidence"
            ],
            'consistency_high': [
                "Very consistent performance across sessions",
                "Excellent stability in your metrics",
                "Your practice is showing great consistency"
            ],
            'consistency_low': [
                "Performance varies between sessions - focus on consistency",
                "Try to maintain steady performance across sessions",
                "Consider establishing a consistent practice routine"
            ],
            'plateau_detected': [
                "Performance has plateaued - try new practice techniques",
                "Time to vary your approach to break through plateau",
                "Consider changing practice methods to continue improving"
            ],
            'milestone_reached': [
                "Congratulations! You've reached a new milestone",
                "Excellent achievement in your practice journey",
                "Milestone unlocked: {milestone}"
            ]
        }
    
    def generate_session_insights(self, session_metrics: Dict[str, Any], goal: str) -> List[str]:
        """
        Generate insights for a single session
        """
        insights = []
        
        try:
            # WPM insights
            wpm = session_metrics.get('wpm', 0)
            if wpm >= 140:
                insights.append("Excellent speaking rate - very natural and engaging")
            elif wpm >= 120:
                insights.append("Good speaking rate - clear and understandable")
            elif wpm < 100:
                insights.append("Consider increasing your speaking rate for better engagement")
            
            # Filler words insights
            filler_ratio = session_metrics.get('filler_ratio', 1.0)
            if filler_ratio <= 0.03:
                insights.append("Outstanding control over filler words!")
            elif filler_ratio <= 0.08:
                insights.append("Good control of filler words")
            elif filler_ratio > 0.15:
                insights.append("Focus on reducing filler words in future sessions")
            
            # Confidence insights
            confidence = session_metrics.get('confidence_score', 0)
            if confidence >= 0.8:
                insights.append("High confidence level - excellent delivery")
            elif confidence >= 0.6:
                insights.append("Good confidence - keep building on this")
            elif confidence < 0.4:
                insights.append("Confidence needs improvement - keep practicing")
            
            # Goal-specific insights
            if goal == "reduce_fillers":
                if filler_ratio <= 0.05:
                    insights.append("Great progress on your filler word reduction goal!")
            elif goal == "improve_fluency":
                if wpm >= 130 and filler_ratio <= 0.08:
                    insights.append("Excellent fluency - balanced pace and minimal fillers")
            elif goal == "interview_practice":
                if confidence >= 0.7 and filler_ratio <= 0.1:
                    insights.append("Strong interview performance - confident and clear")
            
            return insights[:3]  # Limit to 3 insights
        
        except Exception as e:
            logger.error(f"Session insights generation failed: {e}")
            return ["Unable to generate session insights"]
    
    def generate_trend_insights(self, trend_data: List[Dict[str, Any]], metric: str) -> List[str]:
        """
        Generate insights based on trend data
        """
        insights = []
        
        if not trend_data or len(trend_data) < 2:
            return ["Need more data to analyze trends"]
        
        try:
            values = [item.get(metric, 0) for item in trend_data]
            
            # Calculate trend
            if len(values) >= 2:
                change = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
                
                if metric == 'wpm':
                    if change > 10:
                        insights.append(f"Speaking rate improved by {change:.0f}%")
                    elif change < -10:
                        insights.append(f"Speaking rate decreased by {abs(change):.0f}%")
                
                elif metric == 'filler_ratio':
                    if change < -20:
                        insights.append(f"Filler words reduced by {abs(change):.0f}%")
                    elif change > 20:
                        insights.append(f"Filler words increased by {change:.0f}%")
                
                elif metric == 'confidence_score':
                    if change > 15:
                        insights.append("Confidence has significantly improved")
                    elif change < -15:
                        insights.append("Confidence has declined - focus on rebuilding")
            
            # Consistency insights
            if len(values) >= 5:
                import numpy as np
                std_dev = np.std(values)
                mean_val = np.mean(values)
                cv = std_dev / mean_val if mean_val > 0 else 0
                
                if cv < 0.1:
                    insights.append(f"Very consistent {metric}")
                elif cv > 0.3:
                    insights.append(f"{metric.replace('_', ' ').title()} shows high variability")
            
            return insights[:2]  # Limit to 2 insights
        
        except Exception as e:
            logger.error(f"Trend insights generation failed: {e}")
            return ["Unable to analyze trends"]
    
    def generate_goal_insights(self, sessions_data: List[Dict[str, Any]], user_goal: str) -> List[str]:
        """
        Generate goal-specific insights
        """
        insights = []
        
        if not sessions_data:
            return ["Start practicing to see goal-specific insights"]
        
        try:
            # Analyze progress toward goal
            if user_goal == "reduce_fillers":
                filler_ratios = [s.get('filler_ratio', 1.0) for s in sessions_data]
                if filler_ratios:
                    avg_filler = sum(filler_ratios) / len(filler_ratios)
                    if avg_filler <= 0.05:
                        insights.append("Excellent progress on filler word reduction!")
                    elif avg_filler <= 0.1:
                        insights.append("Good progress on reducing filler words")
                    else:
                        insights.append("Continue focusing on reducing filler words")
            
            elif user_goal == "improve_fluency":
                wpm_values = [s.get('wpm', 0) for s in sessions_data]
                filler_ratios = [s.get('filler_ratio', 1.0) for s in sessions_data]
                
                if wpm_values and filler_ratios:
                    avg_wpm = sum(wpm_values) / len(wpm_values)
                    avg_filler = sum(filler_ratios) / len(filler_ratios)
                    
                    if avg_wpm >= 130 and avg_filler <= 0.08:
                        insights.append("Great fluency achieved - balanced pace and minimal fillers")
                    elif avg_wpm < 120:
                        insights.append("Work on increasing speaking rate for better fluency")
                    elif avg_filler > 0.1:
                        insights.append("Reduce filler words to improve fluency")
            
            elif user_goal == "interview_practice":
                confidence_scores = [s.get('confidence_score', 0) for s in sessions_data]
                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    if avg_confidence >= 0.7:
                        insights.append("Strong interview presence - confident and articulate")
                    else:
                        insights.append("Build confidence for better interview performance")
            
            elif user_goal == "presentation_practice":
                pitch_variances = [s.get('pitch_variance', 0) for s in sessions_data]
                if pitch_variances:
                    avg_pitch = sum(pitch_variances) / len(pitch_variances)
                    if avg_pitch >= 150:
                        insights.append("Good vocal variety for presentations")
                    else:
                        insights.append("Add more vocal variety to engage your audience")
            
            return insights[:2]  # Limit to 2 insights
        
        except Exception as e:
            logger.error(f"Goal insights generation failed: {e}")
            return ["Unable to generate goal-specific insights"]
    
    def generate_motivational_insights(self, total_sessions: int, practice_hours: float) -> List[str]:
        """
        Generate motivational insights based on practice statistics
        """
        insights = []
        
        try:
            # Session milestones
            if total_sessions >= 50:
                insights.append("Incredible dedication - 50+ sessions completed!")
            elif total_sessions >= 25:
                insights.append("Great commitment - 25+ sessions completed!")
            elif total_sessions >= 10:
                insights.append("Good progress - 10+ sessions completed!")
            elif total_sessions >= 5:
                insights.append("Nice start - keep up the momentum!")
            
            # Time milestones
            if practice_hours >= 20:
                insights.append("20+ hours of practice - you're becoming an expert!")
            elif practice_hours >= 10:
                insights.append("10+ hours of dedicated practice")
            elif practice_hours >= 5:
                insights.append("Building a solid practice foundation")
            
            # Consistency encouragement
            if total_sessions >= 3:
                insights.append("Consistent practice is the key to improvement")
            
            return insights[:2]  # Limit to 2 insights
        
        except Exception as e:
            logger.error(f"Motivational insights generation failed: {e}")
            return ["Keep up the great work!"]
    
    def generate_actionable_recommendations(self, recent_metrics: Dict[str, Any], goal: str) -> List[str]:
        """
        Generate actionable recommendations for improvement
        """
        recommendations = []
        
        try:
            wpm = recent_metrics.get('wpm', 0)
            filler_ratio = recent_metrics.get('filler_ratio', 1.0)
            confidence = recent_metrics.get('confidence_score', 0)
            pitch_variance = recent_metrics.get('pitch_variance', 0)
            
            # WPM recommendations
            if wpm < 120:
                recommendations.append("Practice speaking at 140-160 WPM for better engagement")
            elif wpm > 180:
                recommendations.append("Slow down slightly for better clarity")
            
            # Filler word recommendations
            if filler_ratio > 0.1:
                recommendations.append("Use deliberate pauses instead of filler words")
                recommendations.append("Practice with a metronome to improve rhythm")
            elif filler_ratio > 0.05:
                recommendations.append("Focus on eliminating the most common filler words")
            
            # Confidence recommendations
            if confidence < 0.5:
                recommendations.append("Practice in front of a mirror to build confidence")
                recommendations.append("Record yourself and review for improvement areas")
            
            # Pitch variance recommendations
            if pitch_variance < 100:
                recommendations.append("Add vocal variety by emphasizing key points")
            elif pitch_variance > 400:
                recommendations.append("Work on more consistent pitch modulation")
            
            # Goal-specific recommendations
            if goal == "interview_practice":
                recommendations.append("Practice common interview questions")
                recommendations.append("Work on structuring answers clearly")
            elif goal == "presentation_practice":
                recommendations.append("Practice storytelling techniques")
                recommendations.append("Work on opening and closing statements")
            
            return recommendations[:3]  # Limit to 3 recommendations
        
        except Exception as e:
            logger.error(f"Actionable recommendations generation failed: {e}")
            return ["Continue practicing to see improvement"]


# Global instance
insights_generator = InsightsGenerator()
