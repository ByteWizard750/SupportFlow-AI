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

# Custom Enterprise CSS for Crisp Alignment & Efficient Space Utilization
st.markdown(
    """
    <style>
    /* Full-width responsive workspace with clean padding */
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* Clean divider baseline */
    hr {
        margin: 0.6rem 0 1rem 0;
        border-color: rgba(255, 255, 255, 0.08);
    }
    
    /* Reduce unnecessary vertical padding in containers */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0;
    }
    
    /* Harmonize expander styling */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
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
