"""
Human-in-the-Loop Agent Workflow Service for SupportFlow AI.

Manages agent draft responses, validates status transitions across the ticket lifecycle
(New -> AI Analyzed -> In Progress -> Resolved), and orchestrates ticket resolution.
"""

from typing import Dict, Any, Tuple, Optional
from database.database import (
    get_ticket_by_id,
    update_ticket_status,
    save_agent_response,
    get_agent_response,
    mark_ticket_resolved,
    get_ticket_analysis,
    get_suggested_response,
)

# Valid Ticket Statuses in SupportFlow AI
VALID_STATUSES = {"New", "AI Analyzed", "In Progress", "Resolved"}

# Permitted Status Transitions
ALLOWED_TRANSITIONS = {
    "New": {"AI Analyzed", "In Progress", "Resolved"},
    "AI Analyzed": {"In Progress", "Resolved"},
    "In Progress": {"Resolved", "In Progress"},
    "Resolved": {"Resolved"},  # Terminal status unless explicitly reopened
}


def validate_status_transition(current_status: str, target_status: str) -> Tuple[bool, str]:
    """
    Validates whether a ticket status transition is permitted by business rules.
    Prevents arbitrary destructive state changes.
    """
    if target_status not in VALID_STATUSES:
        return False, f"Invalid target status '{target_status}'. Must be one of {VALID_STATUSES}."

    if current_status not in VALID_STATUSES:
        return False, f"Invalid current status '{current_status}'."

    if current_status == target_status:
        return True, "No status change needed."

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status in allowed:
        return True, ""

    return False, f"Transition from '{current_status}' to '{target_status}' is not permitted."


def save_agent_draft(
    ticket_id: int,
    agent_response: str,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Saves or updates a draft response edited by the human support agent.
    Does not modify the ticket's primary status.
    """
    if not agent_response or not agent_response.strip():
        return False, "Agent response draft cannot be empty."

    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    if not ticket:
        return False, f"Ticket #{ticket_id} does not exist."

    try:
        save_agent_response(
            ticket_id=ticket_id,
            agent_response=agent_response.strip(),
            status="Draft",
            db_path=db_path
        )
        return True, "Agent draft response saved successfully."
    except Exception as e:
        return False, f"Database error saving agent draft: {str(e)}"


def mark_in_progress(
    ticket_id: int,
    agent_response: Optional[str] = None,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Transitions a ticket to 'In Progress' status to indicate an agent is actively working on it.
    Optionally saves the current draft text if provided.
    """
    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    if not ticket:
        return False, f"Ticket #{ticket_id} does not exist."

    current_status = ticket["status"]
    is_valid, msg = validate_status_transition(current_status, "In Progress")
    if not is_valid:
        return False, msg

    try:
        if agent_response and agent_response.strip():
            save_agent_response(
                ticket_id=ticket_id,
                agent_response=agent_response.strip(),
                status="In Progress",
                db_path=db_path
            )

        update_ticket_status(ticket_id, "In Progress", db_path=db_path)
        return True, f"Ticket #{ticket_id} moved to 'In Progress'."
    except Exception as e:
        return False, f"Database error updating status: {str(e)}"


def resolve_ticket(
    ticket_id: int,
    final_response: str,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Marks a ticket as 'Resolved' with the human support agent's approved/edited final response.
    Stamps resolved_at timestamp in SQLite.
    """
    if not final_response or not final_response.strip():
        return False, "A final resolution response is required to mark the ticket as resolved."

    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    if not ticket:
        return False, f"Ticket #{ticket_id} does not exist."

    current_status = ticket["status"]
    is_valid, msg = validate_status_transition(current_status, "Resolved")
    if not is_valid:
        return False, msg

    try:
        ok = mark_ticket_resolved(
            ticket_id=ticket_id,
            agent_response=final_response.strip(),
            db_path=db_path
        )
        if ok:
            return True, f"Ticket #{ticket_id} has been marked as Resolved."
        return False, "Database update returned no modified rows."
    except Exception as e:
        return False, f"Database error resolving ticket: {str(e)}"


def get_agent_workspace_data(
    ticket_id: int,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assembles complete workspace data for the Agent Review & Resolution panel:
    - ticket: Core ticket fields
    - analysis: AI metadata (category, priority, sentiment, department)
    - suggested_res: RAG grounded draft & sources
    - resolution: Agent's saved draft/resolution
    """
    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    analysis = get_ticket_analysis(ticket_id, db_path=db_path) if ticket else None
    suggested_res = get_suggested_response(ticket_id, db_path=db_path) if ticket else None
    resolution = get_agent_response(ticket_id, db_path=db_path) if ticket else None

    # Determine initial text for agent editor:
    # 1. Previously saved agent draft/resolution
    # 2. Otherwise, RAG AI suggested response
    # 3. Otherwise, empty string
    initial_text = ""
    if resolution and resolution.get("agent_response"):
        initial_text = resolution["agent_response"]
    elif suggested_res and suggested_res.get("suggested_response"):
        initial_text = suggested_res["suggested_response"]

    return {
        "ticket": ticket,
        "analysis": analysis,
        "suggested_res": suggested_res,
        "resolution": resolution,
        "initial_text": initial_text,
        "is_resolved": ticket.get("status") == "Resolved" if ticket else False,
    }
