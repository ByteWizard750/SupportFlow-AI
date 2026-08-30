"""
SQLite Database Layer for SupportFlow AI.

Handles database initialization, connection lifecycle, and CRUD operations
for support tickets and AI ticket analysis records.
"""

import os
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
    Creates the 'tickets' and 'ticket_analyses' tables.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Tickets Table
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
        
        # Insert or Replace analysis record
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

        # Update ticket status if it's currently 'New'
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
