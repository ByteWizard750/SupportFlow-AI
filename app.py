"""
SupportFlow AI — Main Application Entry Point.

Configures Streamlit page setup, modern page navigation,
database initialization, and knowledge base vector index preparation.
"""

import streamlit as st
from database.database import init_db
from services.rag_service import build_vector_index

# Page Configuration
st.set_page_config(
    page_title="SupportFlow AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS for Crisp Alignment & Modern Proportions
st.markdown(
    """
    <style>
    /* Clean container padding and font baseline */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1300px;
    }
    
    /* Harmonize tabs styling */
    div[data-testid="stTabs"] button {
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
    }
    
    /* Ensure disabled text areas are clean and easily readable */
    div[data-baseweb="textarea"] textarea:disabled {
        opacity: 0.92 !important;
        -webkit-text-fill-color: inherit !important;
    }
    
    /* Streamlit divider alignment */
    hr {
        margin: 0.75rem 0 1.25rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Database Schema
init_db()

# Prepare Knowledge Base Index
try:
    build_vector_index()
except Exception as e:
    print(f"[WARN] Vector index auto-build deferred: {e}")

# Sidebar Header Branding
with st.sidebar:
    st.markdown("### SupportFlow AI")
    st.caption("AI-Powered Support Operations")
    st.divider()

# Page Navigation Setup
dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    default=True
)

new_ticket_page = st.Page(
    "pages/new_ticket.py",
    title="New Ticket",
    icon=":material/add_box:"
)

tickets_page = st.Page(
    "pages/tickets.py",
    title="Ticket Queue",
    icon=":material/table_rows:"
)

# Run Navigation
pg = st.navigation({
    "Overview": [dashboard_page],
    "Operations": [new_ticket_page, tickets_page]
})

pg.run()
