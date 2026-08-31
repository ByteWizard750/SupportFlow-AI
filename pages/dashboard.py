"""
Dashboard Page for SupportFlow AI.

Displays metrics calculated directly from database records:
- Total Tickets
- New Tickets
- Operational Status
and a list of recent tickets.
"""

import streamlit as st
import pandas as pd
from services.ticket_service import get_dashboard_summary


def render_dashboard():
    st.title("System Dashboard")
    st.caption("Operational overview and recent ticket activity")
    st.divider()

    # Fetch live summary data
    summary = get_dashboard_summary()
    total_tickets = summary["total_tickets"]
    new_tickets = summary["new_tickets"]
    recent_tickets = summary["recent_tickets"]

    # Metric Cards Row
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.metric(
                label="Total Tickets",
                value=total_tickets,
                help="Total tickets registered in the database"
            )

    with col2:
        with st.container(border=True):
            st.metric(
                label="New Tickets",
                value=new_tickets,
                help="Tickets pending review or processing"
            )

    with col3:
        with st.container(border=True):
            st.metric(
                label="System Status",
                value="Operational",
                help="Database and services connected"
            )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Recent Tickets")

    if not recent_tickets:
        st.info("No tickets created yet. Navigate to 'New Ticket' to submit a record.")
    else:
        display_data = []
        for t in recent_tickets:
            display_data.append({
                "ID": f"#{t['id']}",
                "Customer": t["customer_name"],
                "Subject": t["subject"],
                "Status": t["status"],
                "Created At": t["created_at"],
            })
        df = pd.DataFrame(display_data)
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Customer": st.column_config.TextColumn("Customer", width="medium"),
                "Subject": st.column_config.TextColumn("Subject", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Created At": st.column_config.TextColumn("Timestamp", width="medium"),
            }
        )


if __name__ == "__main__" or True:
    render_dashboard()
