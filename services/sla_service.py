"""
SLA Monitoring & Intelligent Escalation Service for SupportFlow AI.

Provides deterministic SLA deadline calculations, breach detection,
at-risk warnings, compliance rate analytics, and rule-based escalation recommendations.
Zero external API calls required for all SLA computations.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import dateutil.parser

# SLA Target Thresholds in Hours by Priority
SLA_TARGET_HOURS: Dict[str, float] = {
    "Critical": 4.0,
    "High": 12.0,
    "Medium": 24.0,
    "Low": 48.0,
}
DEFAULT_SLA_HOURS = 24.0

# At Risk Consumption Threshold (75% of target duration)
AT_RISK_THRESHOLD = 0.75


def get_sla_target_hours(priority: Optional[str]) -> float:
    """
    Returns deterministic SLA target in hours for a given priority level.
    Defaults to 24.0h for unclassified or unrecognized priorities.
    """
    if not priority:
        return DEFAULT_SLA_HOURS
    norm = priority.strip().capitalize()
    return SLA_TARGET_HOURS.get(norm, DEFAULT_SLA_HOURS)


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """
    Safely parses timestamp string or datetime into a UTC datetime object.
    Supports SQLite timestamps ('YYYY-MM-DD HH:MM:SS') and ISO format.
    """
    if not ts:
        return None
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    try:
        dt = dateutil.parser.parse(str(ts))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def calculate_sla_status(
    created_at: Any,
    priority: Optional[str],
    current_status: str,
    resolved_at: Optional[Any] = None,
    current_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculates deterministic SLA status, elapsed time, remaining/breached time,
    and percentage consumption.

    Returns dictionary with:
    - sla_target_hours: float
    - elapsed_hours: float
    - remaining_hours: float (negative if breached)
    - sla_usage_pct: float
    - sla_status: 'On Track' | 'At Risk' | 'Breached' | 'Met'
    - is_breached: bool
    - is_at_risk: bool
    """
    target_hours = get_sla_target_hours(priority)
    created_dt = parse_timestamp(created_at)

    if not created_dt:
        return {
            "sla_target_hours": target_hours,
            "elapsed_hours": 0.0,
            "remaining_hours": target_hours,
            "sla_usage_pct": 0.0,
            "sla_status": "On Track",
            "is_breached": False,
            "is_at_risk": False,
        }

    now_dt = current_time or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    # If ticket is Resolved
    if current_status == "Resolved":
        resolved_dt = parse_timestamp(resolved_at) or now_dt
        duration_seconds = max(0.0, (resolved_dt - created_dt).total_seconds())
        elapsed_hours = round(duration_seconds / 3600.0, 1)
        remaining_hours = round(target_hours - elapsed_hours, 1)
        sla_usage_pct = round((elapsed_hours / target_hours) * 100.0, 1)

        if elapsed_hours <= target_hours:
            status = "Met"
            is_breached = False
        else:
            status = "Breached"
            is_breached = True

        return {
            "sla_target_hours": target_hours,
            "elapsed_hours": elapsed_hours,
            "remaining_hours": remaining_hours,
            "sla_usage_pct": sla_usage_pct,
            "sla_status": status,
            "is_breached": is_breached,
            "is_at_risk": False,
        }

    # If ticket is Unresolved (New, AI Analyzed, In Progress)
    elapsed_seconds = max(0.0, (now_dt - created_dt).total_seconds())
    elapsed_hours = round(elapsed_seconds / 3600.0, 1)
    remaining_hours = round(target_hours - elapsed_hours, 1)
    sla_usage_pct = round((elapsed_hours / target_hours) * 100.0, 1)

    if elapsed_hours >= target_hours:
        status = "Breached"
        is_breached = True
        is_at_risk = False
    elif elapsed_hours >= (AT_RISK_THRESHOLD * target_hours):
        status = "At Risk"
        is_breached = False
        is_at_risk = True
    else:
        status = "On Track"
        is_breached = False
        is_at_risk = False

    return {
        "sla_target_hours": target_hours,
        "elapsed_hours": elapsed_hours,
        "remaining_hours": remaining_hours,
        "sla_usage_pct": sla_usage_pct,
        "sla_status": status,
        "is_breached": is_breached,
        "is_at_risk": is_at_risk,
    }


def format_sla_duration(hours: float) -> str:
    """
    Formats a duration in hours into a clean human-readable string.
    Examples: '45m', '3.5h', '1.8d (44h)'
    """
    abs_hours = abs(hours)
    if abs_hours < 1.0:
        mins = int(round(abs_hours * 60))
        return f"{mins}m"
    elif abs_hours < 24.0:
        return f"{abs_hours:.1f}h"
    else:
        days = abs_hours / 24.0
        return f"{days:.1f}d ({abs_hours:.0f}h)"


def get_escalation_recommendation(
    priority: Optional[str],
    sla_status: str,
    department: Optional[str] = None
) -> str:
    """
    Returns deterministic, rule-based escalation guidance based on severity and SLA status.
    """
    p = (priority or "Medium").strip().capitalize()
    d = department or "Support"

    if sla_status == "Met":
        return "Resolved within SLA target."

    if sla_status == "Breached":
        if p == "Critical":
            return f"SLA breach detected. Immediate management escalation required. Assign senior lead in {d}."
        elif p == "High":
            return f"SLA breach detected. Expedite response and notify {d} team lead immediately."
        elif p == "Medium":
            return f"Review queue delay and assign available support capacity in {d}."
        else:
            return f"SLA exceeded. Schedule agent review for {d}."

    if sla_status == "At Risk":
        if p == "Critical":
            return f"Immediate escalation recommended. Assign senior support agent and notify {d} lead."
        elif p == "High":
            return f"Prioritize agent assignment to prevent SLA breach in {d}."
        elif p == "Medium":
            return f"Monitor progress and prepare response for {d} inquiry."
        else:
            return f"Approaching SLA deadline. Review queue priority in {d}."

    return "Operating within normal SLA parameters."


def calculate_sla_metrics(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches a ticket dictionary with complete SLA metrics, formatted durations,
    and escalation recommendation.
    """
    sla_calc = calculate_sla_status(
        created_at=ticket.get("created_at"),
        priority=ticket.get("priority"),
        current_status=ticket.get("status", "New"),
        resolved_at=ticket.get("resolved_at")
    )

    enriched = dict(ticket)
    enriched.update(sla_calc)
    enriched["formatted_elapsed"] = format_sla_duration(sla_calc["elapsed_hours"])
    
    if sla_calc["remaining_hours"] >= 0:
        enriched["formatted_remaining"] = format_sla_duration(sla_calc["remaining_hours"])
        enriched["breach_duration_str"] = "None"
    else:
        enriched["formatted_remaining"] = f"-{format_sla_duration(abs(sla_calc['remaining_hours']))}"
        enriched["breach_duration_str"] = format_sla_duration(abs(sla_calc["remaining_hours"]))

    enriched["escalation_recommendation"] = get_escalation_recommendation(
        priority=ticket.get("priority"),
        sla_status=sla_calc["sla_status"],
        department=ticket.get("department")
    )

    return enriched


def get_sla_dashboard_data(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Assembles complete SLA intelligence data for the Support Intelligence Dashboard.
    100% deterministic local computation.
    """
    import pandas as pd
    from database.database import (
        get_sla_summary,
        get_at_risk_tickets,
        get_sla_breached_tickets,
        get_escalation_queue_tickets,
    )

    summary = get_sla_summary(db_path=db_path)
    at_risk_tickets = get_at_risk_tickets(limit=10, db_path=db_path)
    breached_tickets = get_sla_breached_tickets(limit=10, db_path=db_path)
    escalation_queue = get_escalation_queue_tickets(limit=10, db_path=db_path)

    # DataFrame for SLA status distribution with standardized order
    status_order = ["On Track", "At Risk", "Breached", "Met"]
    df_dist = pd.DataFrame(summary.get("sla_status_distribution", []))
    if not df_dist.empty:
        df_dist["status"] = pd.Categorical(df_dist["status"], categories=status_order, ordered=True)
        df_dist = df_dist.sort_values("status").reset_index(drop=True)
    else:
        df_dist = pd.DataFrame(columns=["status", "count"])

    return {
        "summary": summary,
        "df_distribution": df_dist,
        "at_risk_tickets": at_risk_tickets,
        "breached_tickets": breached_tickets,
        "escalation_queue": escalation_queue,
        "has_sla_data": summary.get("total_tickets", 0) > 0,
    }

