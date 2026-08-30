"""
Database package for SupportFlow AI.
"""
from .database import (
    init_db,
    get_connection,
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    get_ticket_metrics,
)

__all__ = [
    "init_db",
    "get_connection",
    "create_ticket",
    "get_all_tickets",
    "get_ticket_by_id",
    "get_ticket_metrics",
]
