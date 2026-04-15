"""
recommendation_service.py
Generates AI-powered post-session coaching recommendations
using Groq's free API (Llama 3) based on session metrics.
"""

import logging
import os
from typing import Optional

from groq import Groq

logger = logging.getLogger(__name__)

# ── Groq client (lazy init) ───────────────────────────────────────────────
_client: Optional[Groq] = None


def _get_client() -> Optional[Groq]:
    global _client
    if _client is None:
        from core.config import settings
        api_key = settings.GROQ_API_KEY  # will be None if not set
        
        if not api_key:  # handles both None and empty string safely
            logger.warning("GROQ_API_KEY not set — using rule-based fallback")
            return None
            
        _client = Groq(api_key=api_key)
    return _client

# ── Prompt builder ────────────────────────────────────────────────────────

def _extract_session_metrics(session: object) -> Optional[dict]:
    metrics = getattr(session, "metrics", None)
    if metrics is None:
        return None

    return {
        "wpm": float(getattr(metrics, "wpm", 0) or 0),
        "filler_ratio": float(getattr(metrics, "filler_ratio", 0) or 0),
        "confidence_score": float(getattr(metrics, "confidence_score", 0) or 0),
        "goal_score": float(getattr(metrics, "goal_score", 0) or 0),
    }


def _build_trend_summary(metrics: dict, previous_sessions: list) -> str:
    if not previous_sessions:
        return "Trend summary: this is the user's first analyzed session."

    previous_metrics = []
    for session in previous_sessions[1:6]:
        extracted = _extract_session_metrics(session)
        if extracted:
            previous_metrics.append(extracted)

    if not previous_metrics:
        return "Trend summary: limited previous session data is available."

    latest_previous = previous_metrics[-1]
    average_previous = {
        key: sum(item[key] for item in previous_metrics) / len(previous_metrics)
        for key in latest_previous
    }

    current_wpm = float(metrics.get("wpm", 0) or 0)
    current_filler_ratio = float(metrics.get("filler_ratio", 0) or 0)
    current_confidence = float(metrics.get("confidence_score", 0) or 0)
    current_goal_score = float(metrics.get("goal_score", 0) or 0)

    return (
        "Trend summary over the last {} analyzed sessions:\n"
        "- Current vs previous session: WPM {:+.1f}, filler ratio {:+.2f}%, confidence {:+.2f}, goal score {:+.2f}\n"
        "- Current vs last {}-session average: WPM {:+.1f}, filler ratio {:+.2f}%, confidence {:+.2f}, goal score {:+.2f}"
    ).format(
        len(previous_metrics),
        current_wpm - latest_previous["wpm"],
        (current_filler_ratio - latest_previous["filler_ratio"]) * 100,
        current_confidence - latest_previous["confidence_score"],
        current_goal_score - latest_previous["goal_score"],
        len(previous_metrics),
        current_wpm - average_previous["wpm"],
        (current_filler_ratio - average_previous["filler_ratio"]) * 100,
        current_confidence - average_previous["confidence_score"],
        current_goal_score - average_previous["goal_score"],
    )

def _build_prompt(metrics: dict, goal: str, previous_sessions: list) -> str:
    """Build a structured prompt from session metrics."""

    # Current session stats
    wpm           = metrics.get("wpm", 0)
    filler_count  = metrics.get("filler_count", 0)
    filler_ratio  = metrics.get("filler_ratio", 0)
    filler_breakdown = metrics.get("filler_breakdown", {})
    confidence    = metrics.get("confidence_score", 0)
    emotion       = metrics.get("emotion_label", "neutral")
    goal_score    = metrics.get("goal_score", 0)
    avg_pause     = metrics.get("avg_pause", 0)
    duration      = metrics.get("duration", 0)

    # Format filler breakdown
    filler_breakdown = metrics.get("filler_breakdown")
    filler_detail = "none detected"

    try:
        if isinstance(filler_breakdown, dict) and filler_breakdown:
            filler_detail = ", ".join(
                f"'{k}' x{v}"
                for k, v in sorted(
                    filler_breakdown.items(), 
                    key=lambda x: -x[1]
                )
            )
        elif isinstance(filler_breakdown, (list, tuple)) and filler_breakdown:
            first = filler_breakdown[0]
            if isinstance(first, dict) and "word" in first and "count" in first:
                # list of dicts like [{"word": "um", "count": 3}, ...]
                filler_detail = ", ".join(
                    f"'{item['word']}' x{item['count']}"
                    for item in filler_breakdown
                )
            elif isinstance(first, (list, tuple)) and len(first) == 2:
                # list of [word, count] pairs
                filler_detail = ", ".join(
                    f"'{item[0]}' x{item[1]}"
                    for item in sorted(
                        filler_breakdown, key=lambda x: -x[1]
                    )
                )
            elif isinstance(first, str):
                # plain list of words
                filler_detail = ", ".join(f"'{w}'" for w in filler_breakdown)
            else:
                filler_detail = str(filler_breakdown)
    except Exception:
        filler_detail = "breakdown unavailable"

    # Format goal nicely
    goal_display = goal.replace("_", " ").title()

    trend_text = _build_trend_summary(metrics, previous_sessions)

    prompt = f"""You are an expert speech coach reviewing a practice session. 
Analyse these metrics and give the user 3 specific, actionable coaching recommendations.

SESSION DETAILS:
- Practice goal: {goal_display}
- Session duration: {round(duration / 60, 1)} minutes

SPEECH METRICS:
- Speaking pace: {round(wpm)} words per minute
  (Ideal range: 110–150 wpm for most goals)
- Filler words: {filler_count} total ({round(filler_ratio * 100, 1)}% of speech)
  Breakdown: {filler_detail}
- Average pause length: {round(avg_pause, 2)} seconds
- Confidence score: {round(confidence, 2)} / 1.0
- Detected emotion/tone: {emotion}
- Goal achievement score: {round(goal_score * 100, 1)}%

HISTORICAL CONTEXT:
{trend_text}

INSTRUCTIONS:
- Give exactly 3 recommendations
- Each recommendation must be specific to the metrics above
- At least one recommendation must explicitly reference how this session compares to the user's previous sessions
- Reference actual numbers from their session (e.g. "your 8% filler rate")
- Be encouraging but honest
- Each recommendation should have: what to work on, why it matters, one concrete exercise
- Keep total response under 250 words
- Format as:
  1. [Title]: [Recommendation]
  2. [Title]: [Recommendation]  
  3. [Title]: [Recommendation]

Do not add any preamble or closing remarks — just the 3 numbered recommendations."""

    return prompt


# ── Main function ──────────────────────────────────────────────────────────

def generate_session_recommendations(
    metrics: dict,
    goal: str,
    previous_sessions: list = [],
) -> dict:
    """
    Generate AI coaching recommendations for a completed session.

    Returns:
    {
        "recommendations": "1. Title: ...\n2. Title: ...\n3. Title: ...",
        "source": "groq" | "fallback",
        "model": "llama-3.1-8b-instant" | "rule_based"
    }
    """
    client = _get_client()

    # ── Try Groq AI first ─────────────────────────────────────────────────
    if client:
        try:
            prompt = _build_prompt(metrics, goal, previous_sessions)

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",   # free, fast, capable
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional speech coach. "
                            "You give specific, data-driven, encouraging feedback. "
                            "You always reference the user's actual numbers."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=400,
            )

            recommendation_text = response.choices[0].message.content.strip()
            logger.info("AI recommendations generated successfully via Groq")

            return {
                "recommendations": recommendation_text,
                "source": "groq",
                "model": "llama-3.1-8b-instant",
            }

        except Exception as e:
            logger.error(f"Groq API call failed: {e} — falling back to rules")

    # ── Rule-based fallback (no API key or API failure) ───────────────────
    return _rule_based_fallback(metrics, goal, previous_sessions)


def _rule_based_fallback(metrics: dict, goal: str, previous_sessions: list = None) -> dict:
    """
    Simple rule-based recommendations when AI is unavailable.
    Keeps the app working even without an API key.
    """
    wpm          = metrics.get("wpm", 130)
    filler_ratio = metrics.get("filler_ratio", 0)
    confidence   = metrics.get("confidence_score", 0.5)
    goal_score   = metrics.get("goal_score", 0.5)
    previous_sessions = previous_sessions or []

    tips = []

    if len(previous_sessions) > 1:
        previous_metrics = _extract_session_metrics(previous_sessions[1])
        if previous_metrics:
            wpm_change = wpm - previous_metrics["wpm"]
            filler_change = (filler_ratio - previous_metrics["filler_ratio"]) * 100
            tips.append(
                f"1. Compare to Your Last Session: WPM changed by {wpm_change:+.1f} and filler ratio changed by {filler_change:+.1f} percentage points. Keep the winning habit from the better metric and tighten the weaker one."
            )

    # Pace
    if wpm > 160:
        tips.append(
            f"{len(tips) + 1}. Slow Your Pace: You spoke at "
            f"{round(wpm)} wpm — above the ideal 110–150 range. "
            "Practice the 'pause and breathe' technique: after every key point, "
            "take one full breath before continuing."
        )
    elif wpm < 100:
        tips.append(
            f"{len(tips) + 1}. Build Your Momentum: Your pace of "
            f"{round(wpm)} wpm feels slow. "
            "Try reading a passage aloud while keeping a steady rhythm — "
            "aim for one word per beat of a 120 BPM metronome."
        )
    else:
        tips.append(
            f"{len(tips) + 1}. Great Pace: Your speaking rate of "
            f"{round(wpm)} wpm is in the ideal range. "
            "Focus on varying your speed slightly to emphasise key points."
        )

    # Fillers
    if filler_ratio > 0.05:
        tips.append(
            f"{len(tips) + 1}. Reduce Filler Words: {round(filler_ratio * 100, 1)}% of your speech "
            "was filler words. Replace them with deliberate silence — "
            "record yourself for 60 seconds and count every 'um' and 'uh' you use."
        )
    else:
        tips.append(
            f"{len(tips) + 1}. Clean Delivery: Your filler word usage is low — well done. "
            "Keep practising pausing deliberately instead of filling silence."
        )

    # Confidence
    if confidence < 0.5:
        tips.append(
            f"{len(tips) + 1}. Build Confidence: Your confidence score was {round(confidence, 2)}. "
            "Try the 'power pose' for 2 minutes before your next session, "
            "and focus on ending sentences with a firm downward tone."
        )
    else:
        tips.append(
            f"{len(tips) + 1}. Strong Presence: Your confidence score of {round(confidence, 2)} "
            "is solid. Push further by practising with an audience — "
            "even presenting to one friend makes a measurable difference."
        )

    return {
        "recommendations": "\n".join(tips),
        "source": "fallback",
        "model": "rule_based",
    }
