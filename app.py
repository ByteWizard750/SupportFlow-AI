"""
SupportFlow AI — Main Application Entry Point.

Configures Streamlit page setup, modern page navigation,
database initialization, and knowledge base vector index preparation.
"""

import streamlit as st
from database.database import init_db
from services.rag_service import build_vector_index, get_embedding_model

# Page Configuration
st.set_page_config(
    page_title="SupportFlow AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS for Balanced Margins, Compact Spacing & Zero Overflow
st.markdown(
    """
    <style>
    /* Centered responsive container with equal left & right margins */
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1280px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Clean divider baseline */
    hr {
        margin: 0.5rem 0 0.85rem 0;
        border-color: rgba(255, 255, 255, 0.08);
    }
    
    /* Custom Compact KPI Card styling */
    .sf-kpi-card {
        background-color: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 10px 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 86px;
    }
    .sf-kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .sf-kpi-val {
        font-size: 1.55rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
        margin: 2px 0;
    }
    .sf-kpi-sub {
        font-size: 0.72rem;
        color: #64748b;
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

# Pre-warm Embedding Model & Prepare Knowledge Base Index on Startup
try:
    get_embedding_model()
    build_vector_index()
except Exception as e:
    print(f"[WARN] Vector index auto-build deferred: {e}")

# Sidebar Header Branding & Status
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

# Subtle sidebar environment indicator at bottom
with st.sidebar:
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size: 0.72rem; color: #475569; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 0.8rem;">
            <div>SupportFlow AI v1.4.0</div>
            <div style="color: #334155; margin-top: 2px;">SQLite • Gemini Flash • FAISS</div>
        </div>
        """,
        unsafe_allow_html=True
    )
