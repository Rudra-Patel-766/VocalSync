import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class TrendsAnalyzer:
    def __init__(self):
        pass
    
    def calculate_trend_slope(self, values: List[float]) -> Tuple[float, float]:
        """
        Calculate linear regression slope and correlation coefficient
        Returns: (slope, correlation_coefficient)
        """
        if len(values) < 2:
            return 0.0, 0.0
        
        try:
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            return float(slope), float(r_value)
        
        except Exception as e:
            logger.error(f"Trend slope calculation failed: {e}")
            return 0.0, 0.0
    
    def detect_trend_pattern(self, values: List[float]) -> str:
        """
        Detect trend patterns: improving, declining, stable, volatile
        """
        if len(values) < 3:
            return "insufficient_data"
        
        try:
            slope, correlation = self.calculate_trend_slope(values)
            
            # Calculate volatility (standard deviation)
            volatility = np.std(values)
            mean_value = np.mean(values)
            normalized_volatility = volatility / mean_value if mean_value > 0 else 0
            
            # Determine trend based on slope and volatility
            if normalized_volatility > 0.3:
                return "volatile"
            elif abs(slope) < 0.01:
                return "stable"
            elif slope > 0:
                return "improving"
            else:
                return "declining"
        
        except Exception as e:
            logger.error(f"Trend pattern detection failed: {e}")
            return "unknown"
    
    def calculate_moving_average(self, values: List[float], window_size: int = 3) -> List[float]:
        """
        Calculate moving average to smooth out short-term fluctuations
        """
        if len(values) < window_size:
            return values
        
        try:
            moving_avg = []
            for i in range(len(values) - window_size + 1):
                window = values[i:i + window_size]
                moving_avg.append(np.mean(window))
            
            return moving_avg
        
        except Exception as e:
            logger.error(f"Moving average calculation failed: {e}")
            return values
    
    def detect_performance_plateau(self, values: List[float], threshold: float = 0.05) -> bool:
        """
        Detect if performance has plateaued (no significant improvement)
        """
        if len(values) < 5:
            return False
        
        try:
            # Look at the last half of the data
            half_point = len(values) // 2
            recent_values = values[half_point:]
            
            # Calculate the range in recent values
            value_range = np.max(recent_values) - np.min(recent_values)
            mean_value = np.mean(recent_values)
            
            # Check if range is small relative to mean
            relative_range = value_range / mean_value if mean_value > 0 else 0
            
            return relative_range < threshold
        
        except Exception as e:
            logger.error(f"Plateau detection failed: {e}")
            return False
    
    def calculate_improvement_rate(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate various improvement rate metrics
        """
        if len(values) < 2:
            return {
                'overall_improvement': 0.0,
                'recent_improvement': 0.0,
                'improvement_acceleration': 0.0
            }
        
        try:
            # Overall improvement (first to last)
            overall_improvement = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            
            # Recent improvement (last 3 sessions)
            recent_count = min(3, len(values))
            recent_values = values[-recent_count:]
            if len(recent_values) >= 2:
                recent_improvement = ((recent_values[-1] - recent_values[0]) / recent_values[0]) * 100 if recent_values[0] != 0 else 0
            else:
                recent_improvement = 0
            
            # Improvement acceleration (change in improvement rate)
            if len(values) >= 4:
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                first_improvement = ((first_half[-1] - first_half[0]) / first_half[0]) * 100 if first_half[0] != 0 else 0
                second_improvement = ((second_half[-1] - second_half[0]) / second_half[0]) * 100 if second_half[0] != 0 else 0
                
                improvement_acceleration = second_improvement - first_improvement
            else:
                improvement_acceleration = 0
            
            return {
                'overall_improvement': float(overall_improvement),
                'recent_improvement': float(recent_improvement),
                'improvement_acceleration': float(improvement_acceleration)
            }
        
        except Exception as e:
            logger.error(f"Improvement rate calculation failed: {e}")
            return {
                'overall_improvement': 0.0,
                'recent_improvement': 0.0,
                'improvement_acceleration': 0.0
            }
    
    def predict_next_value(self, values: List[float]) -> Optional[float]:
        """
        Predict next value using linear regression
        """
        if len(values) < 3:
            return None
        
        try:
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Predict next value
            next_x = len(values)
            predicted_value = slope * next_x + intercept
            
            return float(predicted_value)
        
        except Exception as e:
            logger.error(f"Value prediction failed: {e}")
            return None
    
    def analyze_consistency(self, values: List[float]) -> Dict[str, Any]:
        """
        Analyze performance consistency
        """
        if len(values) < 3:
            return {
                'consistency_score': 0.5,
                'volatility': 0.0,
                'trend_stability': 0.0
            }
        
        try:
            # Calculate volatility (coefficient of variation)
            mean_value = np.mean(values)
            std_value = np.std(values)
            volatility = std_value / mean_value if mean_value > 0 else 0
            
            # Calculate trend stability (correlation coefficient)
            _, correlation = self.calculate_trend_slope(values)
            trend_stability = abs(correlation)
            
            # Overall consistency score (inverse of volatility, weighted by trend stability)
            consistency_score = (1 - min(volatility, 1.0)) * 0.7 + trend_stability * 0.3
            
            return {
                'consistency_score': float(consistency_score),
                'volatility': float(volatility),
                'trend_stability': float(trend_stability)
            }
        
        except Exception as e:
            logger.error(f"Consistency analysis failed: {e}")
            return {
                'consistency_score': 0.5,
                'volatility': 0.0,
                'trend_stability': 0.0
            }
    
    def get_performance_insights(self, values: List[float], metric_name: str) -> List[str]:
        """
        Generate insights based on trend analysis
        """
        insights = []
        
        if len(values) < 3:
            return ["Need more data to analyze trends"]
        
        try:
            # Trend pattern
            pattern = self.detect_trend_pattern(values)
            
            if pattern == "improving":
                slope, _ = self.calculate_trend_slope(values)
                improvement_rate = self.calculate_improvement_rate(values)
                insights.append(f"{metric_name} is consistently improving")
                if improvement_rate['recent_improvement'] > 10:
                    insights.append(f"Recent improvement is excellent at {improvement_rate['recent_improvement']:.0f}%")
            
            elif pattern == "declining":
                insights.append(f"{metric_name} has been declining - consider reviewing your practice approach")
            
            elif pattern == "stable":
                consistency = self.analyze_consistency(values)
                if consistency['consistency_score'] > 0.8:
                    insights.append(f"{metric_name} is very consistent and stable")
                else:
                    insights.append(f"{metric_name} is stable but could be more consistent")
            
            elif pattern == "volatile":
                insights.append(f"{metric_name} shows high variability - focus on consistency")
            
            # Plateau detection
            if self.detect_performance_plateau(values):
                insights.append(f"{metric_name} may have plateaued - try new practice techniques")
            
            # Prediction
            predicted = self.predict_next_value(values)
            if predicted:
                current = values[-1]
                if predicted > current:
                    insights.append(f"{metric_name} is predicted to improve in next session")
                else:
                    insights.append(f"{metric_name} may need attention in next session")
        
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            insights.append("Unable to generate insights due to analysis error")
        
        return insights[:3]  # Limit to 3 insights


# Global instance
trends_analyzer = TrendsAnalyzer()
