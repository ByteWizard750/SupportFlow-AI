"""
SupportFlow AI — Main Application Entry Point.

Configures Streamlit page setup, modern page navigation,
and database initialization.
"""

import streamlit as st
from database.database import init_db

# Page Configuration
st.set_page_config(
    page_title="SupportFlow AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Schema
init_db()

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
