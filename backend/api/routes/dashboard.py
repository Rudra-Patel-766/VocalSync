from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from db.database import get_db
from db.crud import get_last_15_sessions_with_metrics, get_session_count
from api.routes.auth import get_current_user
from schemas.analytics import AnalyticsResponse, DashboardAnalytics, SkillComparison
from services.analytics.aggregator import analytics_aggregator

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user analytics for the last 15 sessions
    """
    try:
        analytics = analytics_aggregator.aggregate_last_15_sessions(db, current_user.id)
        return analytics
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/dashboard", response_model=DashboardAnalytics)
async def get_dashboard_data(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data
    """
    try:
        # Get analytics
        analytics = analytics_aggregator.aggregate_last_15_sessions(db, current_user.id)
        
        # Get skill comparison
        skill_comparison_data = analytics_aggregator.calculate_skill_comparison(db, current_user.id)
        skill_comparison = [
            SkillComparison(**skill) for skill in skill_comparison_data
        ]
        
        # Get practice stats
        practice_stats = analytics_aggregator.calculate_practice_stats(db, current_user.id)
        
        return DashboardAnalytics(
            trend_data=analytics,
            skill_comparison=skill_comparison,
            total_sessions=practice_stats["total_sessions"],
            practice_hours=practice_stats["practice_hours"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/skill-comparison")
async def get_skill_comparison(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get skill comparison data
    """
    try:
        skill_comparison = analytics_aggregator.calculate_skill_comparison(db, current_user.id)
        return skill_comparison
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get skill comparison: {str(e)}"
        )


@router.get("/practice-stats")
async def get_practice_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get practice statistics
    """
    try:
        practice_stats = analytics_aggregator.calculate_practice_stats(db, current_user.id)
        return practice_stats
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get practice stats: {str(e)}"
        )


@router.get("/insights")
async def get_insights(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized insights
    """
    try:
        # Get last 15 sessions for insights
        sessions = get_last_15_sessions_with_metrics(db, current_user.id)
        
        if not sessions:
            return {
                "insights": ["Start practicing to see personalized insights"],
                "recommendations": ["Begin your first practice session to get recommendations"]
            }
        
        # Extract metrics for analysis
        trend_data = []
        for session in sessions:
            if session.metrics:
                trend_data.append({
                    "session_id": session.id,
                    "date": session.start_time,
                    "wpm": session.metrics.wpm,
                    "filler_ratio": session.metrics.filler_ratio,
                    "confidence_score": session.metrics.confidence_score
                })
        
        # Generate insights using trends analyzer
        from services.analytics.trends import trends_analyzer
        from services.analytics.insights import insights_generator
        
        all_insights = []
        all_recommendations = []
        
        # WPM insights
        wpm_insights = trends_analyzer.get_performance_insights(
            [s["wpm"] for s in trend_data], "Speaking Rate"
        )
        all_insights.extend(wpm_insights)
        
        # Filler ratio insights
        filler_insights = trends_analyzer.get_performance_insights(
            [s["filler_ratio"] for s in trend_data], "Filler Words"
        )
        all_insights.extend(filler_insights)
        
        # Confidence insights
        confidence_insights = trends_analyzer.get_performance_insights(
            [s["confidence_score"] for s in trend_data], "Confidence"
        )
        all_insights.extend(confidence_insights)
        
        # Get goal-specific insights (assuming last session's goal)
        if sessions and sessions[0].goal:
            goal_insights = insights_generator.generate_goal_insights(
                trend_data, sessions[0].goal.value
            )
            all_insights.extend(goal_insights)
        
        # Get motivational insights
        session_count = get_session_count(db, current_user.id)
        practice_stats = analytics_aggregator.calculate_practice_stats(db, current_user.id)
        motivational_insights = insights_generator.generate_motivational_insights(
            session_count, practice_stats["practice_hours"]
        )
        all_insights.extend(motivational_insights)
        
        # Get actionable recommendations
        if trend_data:
            latest_metrics = trend_data[0]  # Most recent session
            goal = sessions[0].goal.value if sessions and sessions[0].goal else "improve_fluency"
            recommendations = insights_generator.generate_actionable_recommendations(
                latest_metrics, goal
            )
            all_recommendations.extend(recommendations)
        
        return {
            "insights": all_insights[:5],  # Limit to 5 insights
            "recommendations": all_recommendations[:3]  # Limit to 3 recommendations
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get insights: {str(e)}"
        )
