"""
Database package for SupportFlow AI.
"""
from .database import (
    init_db,
    get_connection,
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    update_ticket_status,
    save_ticket_analysis,
    get_ticket_analysis,
    save_suggested_response,
    get_suggested_response,
    get_ticket_metrics,
)

__all__ = [
    "init_db",
    "get_connection",
    "create_ticket",
    "get_all_tickets",
    "get_ticket_by_id",
    "update_ticket_status",
    "save_ticket_analysis",
    "get_ticket_analysis",
    "save_suggested_response",
    "get_suggested_response",
    "get_ticket_metrics",
]
