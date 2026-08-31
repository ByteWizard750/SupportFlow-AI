"""
Support Analytics & AI Intelligence Service for SupportFlow AI.

Processes SQL aggregations for dashboard visualization and generates
on-demand operational executive summaries via Google Gemini.
"""

import time
from typing import Dict, List, Any, Tuple, Optional, Union
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import get_gemini_api_key, is_gemini_configured, GEMINI_MODEL_NAME
from database.database import (
    get_analytics_kpis,
    get_category_distribution,
    get_department_distribution,
    get_priority_distribution,
    get_sentiment_distribution,
    get_daily_ticket_volume,
    get_urgent_tickets,
    get_recent_activity,
    get_recent_resolutions,
)


class ExecutiveBriefSchema(BaseModel):
    """
    Pydantic schema enforcing structured JSON output for the executive AI brief.
    """
    key_pain_point: str = Field(
        description="1-2 sentences identifying the primary customer pain point or recurring issue based on recent ticket trends."
    )
    highest_workload_risk: str = Field(
        description="1-2 sentences highlighting the department under highest workload or areas with urgent/critical tickets."
    )
    recommended_action: str = Field(
        description="1-2 sentences proposing a concrete, actionable operational step for support leads or product teams."
    )


def get_dashboard_analytics(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregates all metrics and prepares DataFrames for the Support Intelligence Dashboard.
    100% local SQL execution — zero Gemini API calls.
    """
    kpis = get_analytics_kpis(db_path=db_path)
    categories = get_category_distribution(db_path=db_path)
    departments = get_department_distribution(db_path=db_path)
    priorities = get_priority_distribution(db_path=db_path)
    sentiments = get_sentiment_distribution(db_path=db_path)
    daily_volume = get_daily_ticket_volume(db_path=db_path)
    urgent_tickets = get_urgent_tickets(limit=5, db_path=db_path)
    recent_activity = get_recent_activity(limit=5, db_path=db_path)
    recent_resolutions = get_recent_resolutions(limit=5, db_path=db_path)

    # Convert to clean DataFrames
    df_categories = pd.DataFrame(categories) if categories else pd.DataFrame(columns=["category", "count"])
    df_departments = pd.DataFrame(departments) if departments else pd.DataFrame(columns=["department", "count"])
    
    # Priority DataFrame with standardized order
    priority_order = ["Critical", "High", "Medium", "Low"]
    df_priorities = pd.DataFrame(priorities) if priorities else pd.DataFrame(columns=["priority", "count"])
    if not df_priorities.empty:
        df_priorities["priority"] = pd.Categorical(df_priorities["priority"], categories=priority_order, ordered=True)
        df_priorities = df_priorities.sort_values("priority").reset_index(drop=True)

    # Sentiment DataFrame with standardized order
    sentiment_order = ["Positive", "Neutral", "Negative", "Frustrated"]
    df_sentiments = pd.DataFrame(sentiments) if sentiments else pd.DataFrame(columns=["sentiment", "count"])
    if not df_sentiments.empty:
        df_sentiments["sentiment"] = pd.Categorical(df_sentiments["sentiment"], categories=sentiment_order, ordered=True)
        df_sentiments = df_sentiments.sort_values("sentiment").reset_index(drop=True)

    df_daily = pd.DataFrame(daily_volume) if daily_volume else pd.DataFrame(columns=["date", "count"])

    return {
        "kpis": kpis,
        "categories": categories,
        "departments": departments,
        "priorities": priorities,
        "sentiments": sentiments,
        "df_categories": df_categories,
        "df_departments": df_departments,
        "df_priorities": df_priorities,
        "df_sentiments": df_sentiments,
        "df_daily": df_daily,
        "urgent_tickets": urgent_tickets,
        "recent_activity": recent_activity,
        "recent_resolutions": recent_resolutions,
        "has_data": kpis["total_tickets"] > 0,
        "has_analysis": (kpis["total_tickets"] - kpis["new_tickets"]) > 0,
    }


def generate_executive_brief(
    kpis: Dict[str, Any],
    recent_tickets: List[Dict[str, Any]],
    categories: List[Dict[str, Any]],
    urgent_tickets: List[Dict[str, Any]],
    max_retries: int = 2
) -> Tuple[bool, Union[Dict[str, str], str]]:
    """
    Calls Google Gemini on-demand to synthesize current support metrics into
    exactly three actionable executive insights.

    Returns:
        (True, { "key_pain_point": "...", "highest_workload_risk": "...", "recommended_action": "..." }) on success
        (False, error_message) on failure
    """
    if not is_gemini_configured():
        return False, "Gemini API key is not configured in your .env file."

    if not recent_tickets and kpis.get("total_tickets", 0) == 0:
        return False, "No ticket data available to generate an executive brief."

    api_key = get_gemini_api_key()

    # Format structured context for Gemini
    cat_summary = ", ".join([f"{c['category']} ({c['count']})" for c in categories]) if categories else "None"
    urgent_summary = "; ".join([f"#{t['id']} [{t.get('priority', 'High')}] {t['subject']} ({t.get('category', 'General')})" for t in urgent_tickets]) if urgent_tickets else "None"
    recent_summary = "\n".join([f"- #{t['id']}: {t['subject']} (Status: {t['status']}, Category: {t.get('category', 'Unassigned')})" for t in recent_tickets[:6]])

    prompt = f"""You are an executive customer support operations director for SupportFlow AI.
Analyze the current support metrics and generate an actionable operational brief.

Support Metrics Summary:
- Total Tickets: {kpis.get('total_tickets', 0)}
- Open Tickets: {kpis.get('open_tickets', 0)}
- Pending Triage: {kpis.get('new_tickets', 0)}
- AI Analyzed: {kpis.get('analyzed_tickets', 0)}
- In Progress: {kpis.get('in_progress_tickets', 0)}
- Resolved: {kpis.get('resolved_tickets', 0)}
- Resolution Rate: {kpis.get('resolution_rate_pct', 0.0)}%
- Urgent / Critical Issues: {kpis.get('urgent_tickets', 0)}
- Grounded Response Coverage: {kpis.get('rag_coverage_pct', 0.0)}%
- Top Categories: {cat_summary}
- Urgent Issues: {urgent_summary}

Recent Tickets Sample:
{recent_summary}

Instructions:
Provide a structured executive brief with exactly:
1. key_pain_point: The primary customer friction point or recurring issue.
2. highest_workload_risk: The department under heaviest workload or risk from urgent tickets.
3. recommended_action: A concrete, high-impact operational action for the support team.

Keep each insight concise, professional, data-driven, and clear (1-2 sentences each)."""

    client = genai.Client(api_key=api_key)

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExecutiveBriefSchema,
                    temperature=0.2,
                )
            )

            if not response.text:
                return False, "Gemini API returned an empty response."

            parsed = ExecutiveBriefSchema.model_validate_json(response.text)
            return True, parsed.model_dump()

        except APIError as ae:
            if ae.code == 429 and attempt < max_retries:
                time.sleep(5 * (attempt + 1))
                continue
            elif ae.code == 429:
                return False, "Free-tier rate limit reached. Please wait ~15 seconds and try again."
            return False, f"Gemini API error ({ae.code}): {ae.message}"
        except ValidationError as ve:
            return False, f"Structured output validation error: {str(ve)}"
        except Exception as e:
            if "429" in str(e) and attempt < max_retries:
                time.sleep(5 * (attempt + 1))
                continue
            elif "429" in str(e):
                return False, "Free-tier rate limit reached. Please wait ~15 seconds and try again."
            return False, f"Error generating executive brief: {str(e)}"

    return False, "Executive brief generation timed out after retry attempts."
