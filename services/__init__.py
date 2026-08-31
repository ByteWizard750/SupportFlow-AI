"""
Services package for SupportFlow AI.
"""
from .ticket_service import (
    validate_ticket_input,
    create_ticket,
    get_all_tickets,
    get_ticket_by_id,
    get_ticket_analysis,
    analyze_and_store_ticket,
    retrieve_ticket_knowledge,
    generate_and_store_response,
    get_ticket_suggested_response,
    get_dashboard_summary,
)
from .ai_service import analyze_ticket
from .rag_service import (
    get_embedding_model,
    load_knowledge_base_documents,
    chunk_document,
    build_vector_index,
    retrieve_relevant_chunks,
)
from .response_service import (
    generate_suggested_response,
    extract_deterministic_sources,
)
from .analytics_service import (
    get_dashboard_analytics,
    generate_executive_brief,
    ExecutiveBriefSchema,
)
from .agent_service import (
    save_agent_draft,
    mark_in_progress,
    resolve_ticket,
    validate_status_transition,
    get_agent_workspace_data,
    VALID_STATUSES,
)

__all__ = [
    "validate_ticket_input",
    "create_ticket",
    "get_all_tickets",
    "get_ticket_by_id",
    "get_ticket_analysis",
    "analyze_and_store_ticket",
    "retrieve_ticket_knowledge",
    "generate_and_store_response",
    "get_ticket_suggested_response",
    "get_dashboard_summary",
    "analyze_ticket",
    "get_embedding_model",
    "load_knowledge_base_documents",
    "chunk_document",
    "build_vector_index",
    "retrieve_relevant_chunks",
    "generate_suggested_response",
    "extract_deterministic_sources",
    "get_dashboard_analytics",
    "generate_executive_brief",
    "ExecutiveBriefSchema",
    "save_agent_draft",
    "mark_in_progress",
    "resolve_ticket",
    "validate_status_transition",
    "get_agent_workspace_data",
    "VALID_STATUSES",
]
