"""
SupportFlow AI — Main Application Entry Point.

Configures Streamlit page setup, enterprise design system, modern page navigation,
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

# Global Enterprise Design System (SaaS Dark Theme)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography Reset */
    html, body, [class*="css"], .stMarkdown, .stText, p, span, div {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }

    /* Container Spacing */
    .block-container {
        padding-top: 1.75rem !important;
        padding-bottom: 3rem !important;
        max-width: 1350px !important;
    }

    /* Top Header Section */
    h1 {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 0.2rem !important;
    }
    
    h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    h4, h5, h6 {
        font-weight: 600 !important;
        color: #E2E8F0 !important;
    }

    /* Dividers */
    hr {
        margin: 0.85rem 0 1.25rem 0 !important;
        border-color: rgba(255, 255, 255, 0.08) !important;
    }

    /* Bordered Containers (Cards) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #121722 !important;
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        padding: 0.25rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }

    /* Tabs Styling */
    div[data-testid="stTabs"] {
        margin-top: 0.5rem;
    }
    
    div[data-testid="stTabs"] button {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 6px 6px 0 0 !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #F8FAFC !important;
        border-bottom: 2px solid #6366F1 !important;
    }

    div[data-testid="stTabs"] button:hover {
        color: #E2E8F0 !important;
    }

    /* Buttons */
    div.stButton > button {
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        border-radius: 7px !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.15s ease-in-out !important;
        border: 1px solid #334155 !important;
    }

    div.stButton > button:hover {
        border-color: #6366F1 !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.25) !important;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #6366F1 !important;
        font-weight: 600 !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background: #151C2C;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 12px 16px;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
    }

    /* Inputs & Selectboxes */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] > div {
        border-radius: 7px !important;
        border-color: #334155 !important;
        font-size: 0.88rem !important;
    }

    /* Readonly Message Text Areas */
    div[data-baseweb="textarea"] textarea:disabled {
        background-color: #0F141F !important;
        color: #E2E8F0 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        line-height: 1.55 !important;
    }

    /* Dataframe Table */
    div[data-testid="stDataFrame"] {
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #0B0E14 !important;
        border-right: 1px solid #1E293B !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0E14;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
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
    st.markdown(
        """
        <div style="padding: 4px 0 8px 0;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.02em;">SupportFlow AI</div>
            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">Intelligence & RAG Engine</div>
        </div>
        """,
        unsafe_allow_html=True
    )
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
