"""
SupportFlow AI — Main Application Entry Point (Phase 1).

Configures Streamlit page setup, modern page navigation, global design styles,
and database initialization.
"""

import streamlit as st
from database.database import init_db

# Page Configuration
st.set_page_config(
    page_title="SupportFlow AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Schema
init_db()

# Custom CSS for Enterprise UI
CUSTOM_CSS = """
<style>
    /* Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #f8fafc !important;
    }

    section[data-testid="stSidebar"] a {
        color: #cbd5e1 !important;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8;
        border: none;
        color: white;
    }
    
    /* Input Fields */
    div[data-baseweb="input"], div[data-baseweb="textarea"] {
        border-radius: 8px;
    }
    
    /* Hide Streamlit default header/footer elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Sidebar Branding & Navigation
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 1rem 0.5rem 1.5rem 0.5rem; border-bottom: 1px solid #334155; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                <span style="font-size: 1.75rem;">⚡</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #ffffff; letter-spacing: -0.02em;">
                        SupportFlow AI
                    </h2>
                    <span style="font-size: 0.75rem; color: #38bdf8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                        Phase 1: Foundation
                    </span>
                </div>
            </div>
            <p style="margin: 0.75rem 0 0 0; font-size: 0.8rem; color: #94a3b8; line-height: 1.4;">
                Intelligent Support Ticket Assistant & Workflow System
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    icon=":material/add_circle:"
)

tickets_page = st.Page(
    "pages/tickets.py",
    title="Ticket Queue",
    icon=":material/format_list_bulleted:"
)

# Run Navigation
pg = st.navigation({
    "Overview": [dashboard_page],
    "Operations": [new_ticket_page, tickets_page]
})

pg.run()
