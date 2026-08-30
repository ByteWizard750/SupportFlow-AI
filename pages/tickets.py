"""
Tickets Queue and Detail View for SupportFlow AI (Phase 1).

Displays all submitted tickets in a structured list with filtering and search,
and provides a dedicated inspection panel for viewing full ticket details.
"""

import streamlit as st
import pandas as pd
from services.ticket_service import get_all_tickets, get_ticket_by_id


def render_tickets_page():
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1e293b;">
                Ticket Queue & Details
            </h1>
            <p style="margin: 0.35rem 0 0 0; color: #64748b; font-size: 0.95rem;">
                Browse, search, and inspect customer support tickets
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tickets = get_all_tickets()

    if not tickets:
        st.info("No tickets found in the database. Use the **New Ticket** page to create one.")
        return

    # Filter & Search Controls
    col_search, col_status = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "Search Tickets",
            placeholder="Search by ticket ID, customer name, or subject keywords...",
            label_visibility="collapsed"
        )
    with col_status:
        status_options = ["All Statuses"] + sorted(list({t["status"] for t in tickets}))
        selected_status = st.selectbox(
            "Status Filter",
            options=status_options,
            label_visibility="collapsed"
        )

    # Filter logic
    filtered_tickets = tickets
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_tickets = [
            t for t in filtered_tickets
            if q in str(t["id"]).lower()
            or q in t["customer_name"].lower()
            or q in t["subject"].lower()
            or q in t["description"].lower()
        ]

    if selected_status != "All Statuses":
        filtered_tickets = [t for t in filtered_tickets if t["status"] == selected_status]

    st.markdown(f"**Found {len(filtered_tickets)} ticket(s)**")

    if not filtered_tickets:
        st.warning("No tickets match your search / filter criteria.")
        return

    # Layout: Split into Table / List and Detail Inspector
    col_list, col_detail = st.columns([1, 1.1], gap="large")

    with col_list:
        st.markdown("##### Ticket List")

        # Prepare selectbox options
        ticket_options = {
            f"#{t['id']} — {t['subject'][:35]}... ({t['customer_name']})": t["id"]
            for t in filtered_tickets
        }

        selected_label = st.selectbox(
            "Select a ticket to inspect:",
            options=list(ticket_options.keys()),
            key="selected_ticket_selector"
        )
        selected_id = ticket_options[selected_label]

        # Table overview
        table_rows = []
        for t in filtered_tickets:
            table_rows.append({
                "ID": f"#{t['id']}",
                "Customer": t["customer_name"],
                "Subject": t["subject"],
                "Status": t["status"],
                "Date": t["created_at"]
            })
        df = pd.DataFrame(table_rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Customer": st.column_config.TextColumn("Customer", width="medium"),
                "Subject": st.column_config.TextColumn("Subject", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Date": st.column_config.TextColumn("Created", width="medium"),
            }
        )

    with col_detail:
        st.markdown("##### Ticket Details")
        ticket = get_ticket_by_id(selected_id)

        if ticket:
            # Status Badge Styling
            status_color = "#0284c7" if ticket["status"] == "New" else "#10b981"
            status_bg = "#e0f2fe" if ticket["status"] == "New" else "#d1fae5"

            st.markdown(
                f"""
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 1rem; margin-bottom: 1.25rem;">
                        <div>
                            <span style="font-size: 1.3rem; font-weight: 700; color: #0f172a;">Ticket #{ticket['id']}</span>
                        </div>
                        <div>
                            <span style="background-color: {status_bg}; color: {status_color}; padding: 0.3rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">
                                {ticket['status']}
                            </span>
                        </div>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Customer</div>
                        <div style="font-size: 1.05rem; font-weight: 600; color: #1e293b; margin-top: 0.15rem;">{ticket['customer_name']}</div>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Created At</div>
                        <div style="font-size: 0.9rem; color: #475569; margin-top: 0.15rem;">{ticket['created_at']}</div>
                    </div>

                    <div style="margin-bottom: 1.25rem;">
                        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Subject</div>
                        <div style="font-size: 1.05rem; font-weight: 600; color: #0f172a; margin-top: 0.15rem;">{ticket['subject']}</div>
                    </div>

                    <div>
                        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">Full Description</div>
                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; color: #334155; font-size: 0.95rem; line-height: 1.6; white-space: pre-wrap;">{ticket['description']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.error("Selected ticket could not be loaded.")


if __name__ == "__main__" or True:
    render_tickets_page()
