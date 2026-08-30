"""
Ticket Service Layer for SupportFlow AI.

Provides business logic, input validation, AI analysis orchestration,
RAG knowledge retrieval, and suggested response management.
"""

from typing import Dict, List, Optional, Tuple, Any
from database.database import (
    create_ticket as db_create_ticket,
    get_all_tickets as db_get_all_tickets,
    get_ticket_by_id as db_get_ticket_by_id,
    save_ticket_analysis as db_save_ticket_analysis,
    get_ticket_analysis as db_get_ticket_analysis,
    save_suggested_response as db_save_suggested_response,
    get_suggested_response as db_get_suggested_response,
    get_ticket_metrics as db_get_ticket_metrics,
)
from services.ai_service import analyze_ticket
from services.rag_service import retrieve_relevant_chunks
from services.response_service import generate_suggested_response


def validate_ticket_input(customer_name: str, subject: str, description: str) -> Tuple[bool, str]:
    """
    Validates ticket submission fields.
    Ensures all fields are provided and not solely whitespace.
    """
    if not customer_name or not customer_name.strip():
        return False, "Customer Name is required."
    if not subject or not subject.strip():
        return False, "Subject is required."
    if not description or not description.strip():
        return False, "Ticket Description is required."
    if len(customer_name.strip()) < 2:
        return False, "Customer Name must be at least 2 characters long."
    if len(subject.strip()) < 3:
        return False, "Subject must be at least 3 characters long."
    if len(description.strip()) < 5:
        return False, "Ticket Description must be at least 5 characters long."
    return True, ""


def create_ticket(
    customer_name: str,
    subject: str,
    description: str,
    db_path: Optional[str] = None
) -> Tuple[bool, Any]:
    """
    Validates and persists a new ticket.
    Returns:
        (True, ticket_id) on success
        (False, error_message) on failure
    """
    is_valid, error_msg = validate_ticket_input(customer_name, subject, description)
    if not is_valid:
        return False, error_msg

    try:
        ticket_id = db_create_ticket(
            customer_name=customer_name.strip(),
            subject=subject.strip(),
            description=description.strip(),
            db_path=db_path
        )
        return True, ticket_id
    except Exception as e:
        return False, f"Database error creating ticket: {str(e)}"


def get_all_tickets(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves all tickets.
    """
    try:
        return db_get_all_tickets(db_path=db_path)
    except Exception as e:
        print(f"[ERROR] Failed to fetch tickets: {e}")
        return []


def get_ticket_by_id(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves details for a single ticket.
    """
    try:
        return db_get_ticket_by_id(ticket_id=ticket_id, db_path=db_path)
    except Exception as e:
        print(f"[ERROR] Failed to fetch ticket #{ticket_id}: {e}")
        return None


def get_ticket_analysis(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the AI analysis record for a given ticket ID.
    """
    try:
        return db_get_ticket_analysis(ticket_id=ticket_id, db_path=db_path)
    except Exception as e:
        print(f"[ERROR] Failed to fetch analysis for ticket #{ticket_id}: {e}")
        return None


def analyze_and_store_ticket(
    ticket_id: int,
    db_path: Optional[str] = None
) -> Tuple[bool, Any]:
    """
    Orchestrates AI analysis for a specific ticket:
    1. Fetches ticket details from SQLite.
    2. Runs Gemini LLM structured analysis.
    3. Validates and saves analysis to SQLite.
    4. Updates ticket status to 'AI Analyzed'.

    Returns:
        (True, analysis_dict) on success
        (False, error_message) on failure
    """
    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    if not ticket:
        return False, f"Ticket #{ticket_id} was not found."

    # Execute LLM analysis
    success, result = analyze_ticket(
        subject=ticket["subject"],
        description=ticket["description"]
    )

    if not success:
        return False, result

    analysis_data = result

    # Persist to database
    try:
        db_save_ticket_analysis(
            ticket_id=ticket_id,
            category=analysis_data["category"],
            priority=analysis_data["priority"],
            sentiment=analysis_data["sentiment"],
            department=analysis_data["department"],
            reasoning=analysis_data["reasoning"],
            db_path=db_path
        )
        return True, analysis_data
    except Exception as e:
        return False, f"Database error saving analysis: {str(e)}"


def retrieve_ticket_knowledge(
    ticket_id: int,
    top_k: int = 3,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant knowledge base chunks for a ticket query.
    """
    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    if not ticket:
        return []

    query = f"Subject: {ticket['subject']}\nIssue: {ticket['description']}"
    return retrieve_relevant_chunks(query=query, top_k=top_k)


def generate_and_store_response(
    ticket_id: int,
    db_path: Optional[str] = None
) -> Tuple[bool, Any]:
    """
    Executes the full Phase 3 RAG response pipeline:
    1. Retrieves ticket & analysis details.
    2. Retrieves relevant knowledge base chunks.
    3. Generates grounded suggested response with deterministic source attribution.
    4. Persists the response to SQLite.

    Returns:
        (True, result_dict) on success
        (False, error_message) on failure
    """
    ticket = get_ticket_by_id(ticket_id, db_path=db_path)
    if not ticket:
        return False, f"Ticket #{ticket_id} was not found."

    analysis = get_ticket_analysis(ticket_id, db_path=db_path)
    category = analysis["category"] if analysis else None
    priority = analysis["priority"] if analysis else None

    # Retrieve Knowledge Base Context
    query = f"Subject: {ticket['subject']}\nIssue: {ticket['description']}"
    chunks = retrieve_relevant_chunks(query=query, top_k=3)

    # Generate Grounded Response via Gemini
    success, response_text, sources = generate_suggested_response(
        customer_name=ticket["customer_name"],
        subject=ticket["subject"],
        description=ticket["description"],
        retrieved_chunks=chunks,
        category=category,
        priority=priority
    )

    if not success:
        return False, response_text

    # Persist to Database
    try:
        db_save_suggested_response(
            ticket_id=ticket_id,
            suggested_response=response_text,
            retrieved_sources=sources,
            db_path=db_path
        )
        return True, {
            "suggested_response": response_text,
            "retrieved_sources": sources,
            "chunks": chunks
        }
    except Exception as e:
        return False, f"Database error saving response: {str(e)}"


def get_ticket_suggested_response(
    ticket_id: int,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieves stored RAG suggested response for a ticket.
    """
    try:
        return db_get_suggested_response(ticket_id=ticket_id, db_path=db_path)
    except Exception as e:
        print(f"[ERROR] Failed to fetch suggested response for ticket #{ticket_id}: {e}")
        return None


def get_dashboard_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates summary metrics and retrieves the recent tickets for the dashboard.
    Only derives data from actual database records.
    """
    try:
        metrics = db_get_ticket_metrics(db_path=db_path)
        all_tickets = db_get_all_tickets(db_path=db_path)
        recent_tickets = all_tickets[:5]
        return {
            "total_tickets": metrics["total"],
            "new_tickets": metrics["new"],
            "analyzed_tickets": metrics.get("analyzed", 0),
            "recent_tickets": recent_tickets
        }
    except Exception as e:
        print(f"[ERROR] Failed to compile dashboard summary: {e}")
        return {
            "total_tickets": 0,
            "new_tickets": 0,
            "analyzed_tickets": 0,
            "recent_tickets": []
        }
