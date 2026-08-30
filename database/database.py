"""
SQLite Database Layer for SupportFlow AI.

Handles database initialization, connection lifecycle, and CRUD operations
for support tickets.
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
    Creates the 'tickets' table for Phase 1.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
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


def get_ticket_metrics(db_path: Optional[str] = None) -> Dict[str, int]:
    """
    Calculates Phase 1 primary database metrics:
    - total: Total number of tickets submitted.
    - new: Number of tickets currently in 'New' status.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM tickets;")
        total_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS new_count FROM tickets WHERE status = 'New';")
        new_count = cursor.fetchone()["new_count"]

        return {
            "total": total_count,
            "new": new_count
        }
