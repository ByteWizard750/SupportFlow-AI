"""
SQLite Database Layer for SupportFlow AI.

Handles database initialization, connection lifecycle, and CRUD/aggregation operations
for support tickets, AI ticket analyses, RAG suggested responses, and human agent resolutions.
"""

import os
import json
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "supportflow.db"
)


@contextmanager
def get_connection(db_path: Optional[str] = None):
    """
    Context manager for SQLite database connections.
    Configures Row factory to allow dictionary-like row access.
    """
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes the SQLite database schema if it doesn't already exist.
    Creates 'tickets', 'ticket_analyses', 'ticket_rag_responses', and 'ticket_resolutions' tables.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Tickets Table (Phase 1)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'New',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Ticket Analyses Table (Phase 2)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL UNIQUE,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                department TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );
            """
        )

        # Ticket RAG Suggested Responses Table (Phase 3)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_rag_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL UNIQUE,
                suggested_response TEXT NOT NULL,
                retrieved_sources TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );
            """
        )

        # Ticket Resolutions Table (Phase 5 — Human-in-the-Loop)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_resolutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL UNIQUE,
                agent_response TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Draft',
                resolved_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()


def create_ticket(
    customer_name: str,
    subject: str,
    description: str,
    db_path: Optional[str] = None
) -> int:
    """
    Inserts a new support ticket into the database with default status 'New'.
    Returns the newly created ticket ID.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tickets (customer_name, subject, description, status)
            VALUES (?, ?, ?, 'New');
            """,
            (customer_name.strip(), subject.strip(), description.strip())
        )
        ticket_id = cursor.lastrowid
        return ticket_id


def get_all_tickets(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches all tickets from the database, ordered chronologically (newest first).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, customer_name, subject, description, status, created_at
            FROM tickets
            ORDER BY created_at DESC, id DESC;
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_ticket_by_id(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single ticket by its primary key ID.
    Returns a dictionary of ticket fields, or None if not found.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, customer_name, subject, description, status, created_at
            FROM tickets
            WHERE id = ?;
            """,
            (ticket_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_ticket_status(ticket_id: int, new_status: str, db_path: Optional[str] = None) -> bool:
    """
    Updates the status of a specific ticket.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tickets
            SET status = ?
            WHERE id = ?;
            """,
            (new_status, ticket_id)
        )
        return cursor.rowcount > 0


def save_ticket_analysis(
    ticket_id: int,
    category: str,
    priority: str,
    sentiment: str,
    department: str,
    reasoning: str,
    db_path: Optional[str] = None
) -> int:
    """
    Persists AI analysis metadata for a ticket in 'ticket_analyses'.
    If the ticket was 'New', updates status to 'AI Analyzed'.
    Returns analysis ID.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO ticket_analyses (ticket_id, category, priority, sentiment, department, reasoning, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ticket_id) DO UPDATE SET
                category = excluded.category,
                priority = excluded.priority,
                sentiment = excluded.sentiment,
                department = excluded.department,
                reasoning = excluded.reasoning,
                analyzed_at = CURRENT_TIMESTAMP;
            """,
            (ticket_id, category, priority, sentiment, department, reasoning)
        )
        analysis_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE tickets
            SET status = 'AI Analyzed'
            WHERE id = ? AND status = 'New';
            """,
            (ticket_id,)
        )
        
        return analysis_id


def get_ticket_analysis(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the AI analysis record for a given ticket ID.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, ticket_id, category, priority, sentiment, department, reasoning, analyzed_at
            FROM ticket_analyses
            WHERE ticket_id = ?;
            """,
            (ticket_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def save_suggested_response(
    ticket_id: int,
    suggested_response: str,
    retrieved_sources: List[str],
    db_path: Optional[str] = None
) -> int:
    """
    Persists the AI suggested response and the deterministically retrieved source list.
    """
    sources_json = json.dumps(retrieved_sources)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ticket_rag_responses (ticket_id, suggested_response, retrieved_sources, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ticket_id) DO UPDATE SET
                suggested_response = excluded.suggested_response,
                retrieved_sources = excluded.retrieved_sources,
                created_at = CURRENT_TIMESTAMP;
            """,
            (ticket_id, suggested_response.strip(), sources_json)
        )
        return cursor.lastrowid


def get_suggested_response(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the stored RAG suggested response for a ticket.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, ticket_id, suggested_response, retrieved_sources, created_at
            FROM ticket_rag_responses
            WHERE ticket_id = ?;
            """,
            (ticket_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        data = dict(row)
        try:
            data["retrieved_sources"] = json.loads(data["retrieved_sources"])
        except Exception:
            data["retrieved_sources"] = []
        return data


def get_ticket_metrics(db_path: Optional[str] = None) -> Dict[str, int]:
    """
    Calculates primary database metrics:
    - total: Total number of tickets submitted.
    - new: Number of tickets currently in 'New' status.
    - analyzed: Number of tickets in 'AI Analyzed' status.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM tickets;")
        total_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS new_count FROM tickets WHERE status = 'New';")
        new_count = cursor.fetchone()["new_count"]

        cursor.execute("SELECT COUNT(*) AS analyzed_count FROM tickets WHERE status = 'AI Analyzed';")
        analyzed_count = cursor.fetchone()["analyzed_count"]

        return {
            "total": total_count,
            "new": new_count,
            "analyzed": analyzed_count
        }


# ==================== PHASE 5: HUMAN-IN-THE-LOOP RESOLUTIONS ====================

def save_agent_response(
    ticket_id: int,
    agent_response: str,
    status: str = "Draft",
    db_path: Optional[str] = None
) -> int:
    """
    Saves or updates the human support agent's edited response in 'ticket_resolutions'.
    Does not overwrite or alter the AI suggested response in 'ticket_rag_responses'.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ticket_resolutions (ticket_id, agent_response, status, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ticket_id) DO UPDATE SET
                agent_response = excluded.agent_response,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (ticket_id, agent_response.strip(), status)
        )
        return cursor.lastrowid


def get_agent_response(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the agent's edited response and resolution status for a ticket.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, ticket_id, agent_response, status, resolved_at, updated_at
            FROM ticket_resolutions
            WHERE ticket_id = ?;
            """,
            (ticket_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_ticket_resolution(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Alias for get_agent_response to retrieve complete resolution metadata.
    """
    return get_agent_response(ticket_id, db_path=db_path)


def mark_ticket_resolved(
    ticket_id: int,
    agent_response: str,
    db_path: Optional[str] = None
) -> bool:
    """
    Marks a support ticket as 'Resolved' in SQLite:
    1. Saves the final human agent response in 'ticket_resolutions' with status 'Resolved' and resolved_at timestamp.
    2. Updates the ticket's primary status in 'tickets' table to 'Resolved'.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ticket_resolutions (ticket_id, agent_response, status, resolved_at, updated_at)
            VALUES (?, ?, 'Resolved', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(ticket_id) DO UPDATE SET
                agent_response = excluded.agent_response,
                status = 'Resolved',
                resolved_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (ticket_id, agent_response.strip())
        )

        cursor.execute(
            """
            UPDATE tickets
            SET status = 'Resolved'
            WHERE id = ?;
            """,
            (ticket_id,)
        )
        return cursor.rowcount > 0


def get_recent_resolutions(limit: int = 5, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the most recent resolved tickets with customer details, category, and resolved timestamp.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                t.id, 
                t.customer_name, 
                t.subject, 
                t.status, 
                COALESCE(ta.category, 'General') AS category, 
                tr.agent_response, 
                tr.resolved_at
            FROM tickets t
            JOIN ticket_resolutions tr ON t.id = tr.ticket_id
            LEFT JOIN ticket_analyses ta ON t.id = ta.ticket_id
            WHERE t.status = 'Resolved'
            ORDER BY tr.resolved_at DESC, t.id DESC
            LIMIT ?;
            """,
            (limit,)
        )
        return [dict(r) for r in cursor.fetchall()]


# ==================== PHASE 4 & 5: SQL ANALYTICS AGGREGATIONS ====================

def get_analytics_kpis(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes comprehensive operational lifecycle KPI metrics:
    - total_tickets: Overall volume of tickets
    - open_tickets: Tickets not marked Resolved (New, AI Analyzed, In Progress)
    - new_tickets: Pending triage tickets (status = 'New')
    - analyzed_tickets: Successfully classified tickets (status = 'AI Analyzed')
    - in_progress_tickets: Tickets actively being worked on by human agents (status = 'In Progress')
    - resolved_tickets: Tickets successfully resolved (status = 'Resolved')
    - urgent_tickets: High or Critical priority tickets
    - rag_responses: Tickets with grounded RAG suggestions generated
    - triage_coverage_pct: Percentage of tickets that have been processed beyond 'New'
    - rag_coverage_pct: Percentage of tickets that have generated suggested responses
    - resolution_rate_pct: Percentage of tickets resolved
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM tickets;")
        total = cursor.fetchone()["total"] or 0

        cursor.execute("SELECT COUNT(*) AS new_cnt FROM tickets WHERE status = 'New';")
        new_cnt = cursor.fetchone()["new_cnt"] or 0

        cursor.execute("SELECT COUNT(*) AS analyzed_cnt FROM tickets WHERE status = 'AI Analyzed';")
        analyzed_cnt = cursor.fetchone()["analyzed_cnt"] or 0

        cursor.execute("SELECT COUNT(*) AS in_progress_cnt FROM tickets WHERE status = 'In Progress';")
        in_progress_cnt = cursor.fetchone()["in_progress_cnt"] or 0

        cursor.execute("SELECT COUNT(*) AS resolved_cnt FROM tickets WHERE status = 'Resolved';")
        resolved_cnt = cursor.fetchone()["resolved_cnt"] or 0

        cursor.execute("SELECT COUNT(*) AS open_cnt FROM tickets WHERE status != 'Resolved';")
        open_cnt = cursor.fetchone()["open_cnt"] or 0

        cursor.execute("SELECT COUNT(*) AS urgent_cnt FROM ticket_analyses WHERE priority IN ('High', 'Critical');")
        urgent_cnt = cursor.fetchone()["urgent_cnt"] or 0

        cursor.execute("SELECT COUNT(*) AS rag_cnt FROM ticket_rag_responses;")
        rag_cnt = cursor.fetchone()["rag_cnt"] or 0

        # Triage coverage includes all tickets moved beyond raw 'New' status
        triaged_cnt = total - new_cnt
        triage_coverage = round((triaged_cnt / total * 100.0), 1) if total > 0 else 0.0
        rag_coverage = round((rag_cnt / total * 100.0), 1) if total > 0 else 0.0
        resolution_rate = round((resolved_cnt / total * 100.0), 1) if total > 0 else 0.0

        return {
            "total_tickets": total,
            "open_tickets": open_cnt,
            "new_tickets": new_cnt,
            "analyzed_tickets": analyzed_cnt,
            "in_progress_tickets": in_progress_cnt,
            "resolved_tickets": resolved_cnt,
            "urgent_tickets": urgent_cnt,
            "rag_responses": rag_cnt,
            "triage_coverage_pct": triage_coverage,
            "rag_coverage_pct": rag_coverage,
            "resolution_rate_pct": resolution_rate
        }


def get_category_distribution(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Aggregates ticket count grouped by Category.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM ticket_analyses
            GROUP BY category
            ORDER BY count DESC, category ASC;
            """
        )
        return [dict(r) for r in cursor.fetchall()]


def get_department_distribution(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Aggregates ticket count grouped by Recommended Department.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT department, COUNT(*) AS count
            FROM ticket_analyses
            GROUP BY department
            ORDER BY count DESC, department ASC;
            """
        )
        return [dict(r) for r in cursor.fetchall()]


def get_priority_distribution(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Aggregates ticket count grouped by Priority level.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT priority, COUNT(*) AS count
            FROM ticket_analyses
            GROUP BY priority
            ORDER BY count DESC, priority ASC;
            """
        )
        return [dict(r) for r in cursor.fetchall()]


def get_sentiment_distribution(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Aggregates ticket count grouped by Customer Sentiment.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sentiment, COUNT(*) AS count
            FROM ticket_analyses
            GROUP BY sentiment
            ORDER BY count DESC, sentiment ASC;
            """
        )
        return [dict(r) for r in cursor.fetchall()]


def get_daily_ticket_volume(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Aggregates ticket count grouped by creation date (YYYY-MM-DD).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DATE(created_at) AS date, COUNT(*) AS count
            FROM tickets
            GROUP BY DATE(created_at)
            ORDER BY date ASC;
            """
        )
        return [dict(r) for r in cursor.fetchall()]


def get_urgent_tickets(limit: int = 5, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the most recent tickets flagged as High or Critical priority.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                t.id, 
                t.customer_name, 
                t.subject, 
                t.status, 
                ta.category, 
                ta.priority, 
                ta.department, 
                t.created_at
            FROM tickets t
            JOIN ticket_analyses ta ON t.id = ta.ticket_id
            WHERE ta.priority IN ('High', 'Critical')
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT ?;
            """,
            (limit,)
        )
        return [dict(r) for r in cursor.fetchall()]


def get_recent_activity(limit: int = 5, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the most recent tickets with their category (if analyzed).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                t.id, 
                t.customer_name, 
                t.subject, 
                t.status, 
                COALESCE(ta.category, 'Pending Triage') AS category, 
                t.created_at
            FROM tickets t
            LEFT JOIN ticket_analyses ta ON t.id = ta.ticket_id
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT ?;
            """,
            (limit,)
        )
        return [dict(r) for r in cursor.fetchall()]
