"""
Dashboard Page for SupportFlow AI (Phase 1).

Displays metrics calculated directly from database records:
- Total Tickets
- New Tickets
and a list of recent tickets.
"""

import streamlit as st
import pandas as pd
from services.ticket_service import get_dashboard_summary


def render_dashboard():
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1e293b;">
                System Dashboard
            </h1>
            <p style="margin: 0.35rem 0 0 0; color: #64748b; font-size: 0.95rem;">
                Real-time operational summary of customer support tickets
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch live summary data
    summary = get_dashboard_summary()
    total_tickets = summary["total_tickets"]
    new_tickets = summary["new_tickets"]
    recent_tickets = summary["recent_tickets"]

    # Metric Cards Row
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.85rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">
                    Total Tickets
                </div>
                <div style="font-size: 2.25rem; font-weight: 700; color: #0f172a; margin-top: 0.5rem;">
                    {total_tickets}
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                    All tickets stored in system
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.85rem; font-weight: 600; color: #0284c7; text-transform: uppercase; letter-spacing: 0.05em;">
                    New Tickets
                </div>
                <div style="font-size: 2.25rem; font-weight: 700; color: #0284c7; margin-top: 0.5rem;">
                    {new_tickets}
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                    Awaiting agent review
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.85rem; font-weight: 600; color: #10b981; text-transform: uppercase; letter-spacing: 0.05em;">
                    System Status
                </div>
                <div style="font-size: 2.25rem; font-weight: 700; color: #10b981; margin-top: 0.5rem;">
                    Active
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                    SQLite Database Connected
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)

    # Recent Tickets Section
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <h2 style="font-size: 1.2rem; font-weight: 600; color: #1e293b; margin: 0;">
                Recent Tickets
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not recent_tickets:
        st.info("No support tickets created yet. Use the **New Ticket** page to submit the first ticket.")
    else:
        # Convert to clean dataframe display
        display_data = []
        for t in recent_tickets:
            display_data.append({
                "Ticket ID": f"#{t['id']}",
                "Customer": t["customer_name"],
                "Subject": t["subject"],
                "Status": t["status"],
                "Created At": t["created_at"],
            })
        df = pd.DataFrame(display_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticket ID": st.column_config.TextColumn("ID", width="small"),
                "Customer": st.column_config.TextColumn("Customer Name", width="medium"),
                "Subject": st.column_config.TextColumn("Subject", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Created At": st.column_config.TextColumn("Date / Time", width="medium"),
            }
        )


if __name__ == "__main__" or True:
    render_dashboard()
