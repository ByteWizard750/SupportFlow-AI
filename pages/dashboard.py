"""
Dashboard Page for SupportFlow AI.

Displays operational metrics and recent support ticket activity
in a sleek enterprise cockpit layout.
"""

import streamlit as st
import pandas as pd
from services.ticket_service import get_dashboard_summary


def render_dashboard():
    # Page Header
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5rem;">
            <div>
                <h1 style="margin: 0; font-size: 1.75rem; font-weight: 700;">Operations Dashboard</h1>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">Real-time overview of ticket intake, AI triage throughput, and system health</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()

    # Fetch live summary data
    summary = get_dashboard_summary()
    total_tickets = summary["total_tickets"]
    new_tickets = summary["new_tickets"]
    analyzed_tickets = summary.get("analyzed_tickets", 0)
    recent_tickets = summary["recent_tickets"]

    # 4-Column KPI Metric Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div style="background: #121722; border: 1px solid #1E293B; border-radius: 10px; padding: 14px 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Total Tickets</div>
                <div style="font-size: 26px; font-weight: 700; color: #F8FAFC; margin-top: 4px;">{total_tickets}</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 2px;">All registered records</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: #121722; border: 1px solid #1E293B; border-radius: 10px; padding: 14px 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">New Intake</div>
                <div style="font-size: 26px; font-weight: 700; color: #60A5FA; margin-top: 4px;">{new_tickets}</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 2px;">Pending triage review</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: #121722; border: 1px solid #1E293B; border-radius: 10px; padding: 14px 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">AI Analyzed</div>
                <div style="font-size: 26px; font-weight: 700; color: #34D399; margin-top: 4px;">{analyzed_tickets}</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 2px;">Classified by Gemini</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div style="background: #121722; border: 1px solid #1E293B; border-radius: 10px; padding: 14px 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Knowledge Base</div>
                <div style="font-size: 26px; font-weight: 700; color: #818CF8; margin-top: 4px;">5 Docs</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 2px;">FAISS dense index ready</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
    
    # Recent Tickets Table
    st.markdown(
        """
        <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
            Recent Ticket Activity
        </div>
        """,
        unsafe_allow_html=True
    )

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
            use_container_width=True,
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
