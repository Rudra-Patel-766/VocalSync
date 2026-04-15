import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.session import Session
from models.metrics import SessionMetrics
from schemas.analytics import SessionTrend, AnalyticsResponse
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class AnalyticsAggregator:
    def __init__(self):
        pass
    
    def aggregate_last_15_sessions(self, db: Session, user_id: int) -> AnalyticsResponse:
        try:
            # Get last 15 sessions with metrics
            sessions = db.query(Session).join(SessionMetrics).filter(
                Session.user_id == user_id
            ).order_by(Session.start_time.desc()).limit(15).all()
            
            if not sessions:
                return self._empty_analytics()
            
            # Convert to trend data
            trend_data = []
            for session in sessions:
                trend_data.append(SessionTrend(
                    session_id=session.id,
                    date=session.start_time,
                    wpm=session.metrics.wpm,
                    filler_ratio=session.metrics.filler_ratio,
                    confidence_score=session.metrics.confidence_score
                ))

            # Queries are newest-first; trend math should run oldest -> newest.
            trend_data = list(reversed(trend_data))
            
            # Calculate trends
            wpm_growth = self._calculate_growth_trend([s.wpm for s in trend_data])
            filler_reduction = self._calculate_decline_trend([s.filler_ratio for s in trend_data])
            confidence_trend = self._calculate_trend_direction([s.confidence_score for s in trend_data])
            
            # Generate insights
            insights = self._generate_insights(trend_data)
            
            return AnalyticsResponse(
                last_15_sessions=trend_data,
                wpm_growth=wpm_growth,
                filler_reduction=filler_reduction,
                confidence_trend=confidence_trend,
                insights=insights
            )
        
        except Exception as e:
            logger.error(f"Analytics aggregation failed: {e}")
            return self._empty_analytics()
    
    def _empty_analytics(self) -> AnalyticsResponse:
        return AnalyticsResponse(
            last_15_sessions=[],
            wpm_growth=0.0,
            filler_reduction=0.0,
            confidence_trend="stable",
            insights=["No session data available yet. Start practicing to see your analytics!"]
        )
    
    def _calculate_growth_trend(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        
        try:
            numeric_values = [float(value) for value in values if value is not None]
            if len(numeric_values) < 2:
                return 0.0

            # Calculate linear regression slope
            x = np.arange(len(numeric_values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, numeric_values)
            
            # Calculate percentage growth from first to last
            baseline = next((value for value in numeric_values if abs(value) > 1e-9), None)
            if baseline is None:
                return 0.0

            growth = ((numeric_values[-1] - baseline) / abs(baseline)) * 100
            
            return float(growth)
        
        except Exception as e:
            logger.error(f"Growth trend calculation failed: {e}")
            return 0.0
    
    def _calculate_decline_trend(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        
        try:
            # For filler ratio, we want reduction (negative growth is good)
            growth = self._calculate_growth_trend(values)
            
            # Convert to reduction percentage
            reduction = -growth
            
            return float(reduction)
        
        except Exception as e:
            logger.error(f"Decline trend calculation failed: {e}")
            return 0.0
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        if len(values) < 2:
            return "stable"
        
        try:
            # Calculate linear regression slope
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Determine trend direction based on slope and significance
            if abs(slope) < 0.01:  # Very small slope
                return "stable"
            elif slope > 0:
                return "improving"
            else:
                return "declining"
        
        except Exception as e:
            logger.error(f"Trend direction calculation failed: {e}")
            return "stable"
    
    def _generate_insights(self, trend_data: List[SessionTrend]) -> List[str]:
        insights = []
        
        if not trend_data:
            return insights
        
        # WPM insights
        wpm_values = [s.wpm for s in trend_data]
        avg_wpm = np.mean(wpm_values)
        if len(wpm_values) >= 2:
            baseline_wpm = next((value for value in wpm_values if value > 0), None)
            if baseline_wpm:
                wpm_change = ((wpm_values[-1] - baseline_wpm) / baseline_wpm) * 100
                if wpm_change > 10:
                    insights.append(f"Speaking rate improved by {wpm_change:.0f}%")
                elif wpm_change < -10:
                    insights.append(f"Speaking rate decreased by {abs(wpm_change):.0f}%")
        
        # Filler words insights
        filler_ratios = [s.filler_ratio for s in trend_data]
        avg_filler_ratio = np.mean(filler_ratios)
        if len(filler_ratios) >= 2:
            baseline_filler = next((value for value in filler_ratios if value > 0), None)
            if baseline_filler:
                filler_change = ((filler_ratios[-1] - baseline_filler) / baseline_filler) * 100
                if filler_change < -20:
                    insights.append(f"Filler words reduced by {abs(filler_change):.0f}%")
                elif filler_change > 20:
                    insights.append(f"Filler words increased by {filler_change:.0f}%")
        
        # Confidence insights
        confidence_scores = [s.confidence_score for s in trend_data]
        avg_confidence = np.mean(confidence_scores)
        if len(confidence_scores) >= 6:  # Need enough data for stability analysis
            recent_confidence = confidence_scores[-3:]
            early_confidence = confidence_scores[:3]
            recent_avg = np.mean(recent_confidence)
            early_avg = np.mean(early_confidence)
            
            if recent_avg > early_avg + 0.1:
                insights.append("Confidence significantly improved in recent sessions")
            elif abs(recent_avg - early_avg) < 0.05:
                insights.append("Confidence stabilized after initial sessions")
        
        # Performance consistency
        if len(confidence_scores) >= 5:
            confidence_std = np.std(confidence_scores)
            if confidence_std < 0.1:
                insights.append("Performance is very consistent")
            elif confidence_std > 0.2:
                insights.append("Performance varies significantly between sessions")
        
        # Goal-specific insights
        if avg_wpm < 120:
            insights.append("Consider increasing speaking rate for better engagement")
        elif avg_wpm > 160:
            insights.append("Speaking rate is quite fast - consider slowing down")
        
        if avg_filler_ratio > 0.1:
            insights.append("Focus on reducing filler words in future sessions")
        elif avg_filler_ratio < 0.03:
            insights.append("Excellent control over filler words!")
        
        if not insights:
            insights.append("Keep practicing to see more detailed insights")
        
        return insights[:5]  # Limit to 5 insights
    
    def calculate_skill_comparison(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        try:
            # Get user's sessions
            sessions = db.query(Session).join(SessionMetrics).filter(
                Session.user_id == user_id
            ).all()
            
            if not sessions:
                return []
            
            # Calculate user's averages
            user_metrics = {
                'wpm': np.mean([s.metrics.wpm for s in sessions]),
                'filler_ratio': np.mean([s.metrics.filler_ratio for s in sessions]),
                'confidence_score': np.mean([s.metrics.confidence_score for s in sessions]),
                'pitch_variance': np.mean([s.metrics.pitch_variance for s in sessions])
            }
            
            # Calculate benchmarks (ideal values)
            benchmarks = {
                'wpm': 140,
                'filler_ratio': 0.02,
                'confidence_score': 0.8,
                'pitch_variance': 200
            }
            
            # Calculate improvements
            skill_comparison = []
            for skill, user_value in user_metrics.items():
                benchmark = benchmarks[skill]
                
                if skill == 'filler_ratio':
                    # For filler ratio, lower is better
                    improvement = max(0, (benchmark - user_value) / benchmark) * 100
                else:
                    # For other metrics, higher is better
                    improvement = max(0, (user_value - benchmark) / benchmark) * 100
                
                skill_comparison.append({
                    'skill': skill.replace('_', ' ').title(),
                    'current_value': user_value,
                    'average_value': benchmark,
                    'improvement': improvement
                })
            
            return skill_comparison
        
        except Exception as e:
            logger.error(f"Skill comparison calculation failed: {e}")
            return []
    
    def calculate_practice_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        try:
            # Get all sessions
            sessions = db.query(Session).filter(Session.user_id == user_id).all()
            
            if not sessions:
                return {
                    'total_sessions': 0,
                    'practice_hours': 0.0,
                    'avg_session_duration': 0.0
                }
            
            # Calculate total sessions
            total_sessions = len(sessions)
            
            # Calculate practice hours
            total_duration = 0
            completed_sessions = 0
            
            for session in sessions:
                if session.end_time:
                    duration = (session.end_time - session.start_time).total_seconds()
                    total_duration += duration
                    completed_sessions += 1
            
            practice_hours = total_duration / 3600  # Convert to hours
            avg_session_duration = total_duration / completed_sessions if completed_sessions > 0 else 0
            
            return {
                'total_sessions': total_sessions,
                'practice_hours': practice_hours,
                'avg_session_duration': avg_session_duration
            }
        
        except Exception as e:
            logger.error(f"Practice stats calculation failed: {e}")
            return {
                'total_sessions': 0,
                'practice_hours': 0.0,
                'avg_session_duration': 0.0
            }


# Global instance
analytics_aggregator = AnalyticsAggregator()
