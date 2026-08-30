"""
Tickets Queue and Detail View for SupportFlow AI (Phase 1).

Displays all submitted tickets in a structured list with filtering and search,
and provides a dedicated inspection panel for viewing full ticket details.
"""

import streamlit as st
import pandas as pd
from services.ticket_service import get_all_tickets, get_ticket_by_id


def render_tickets_page():
    st.title("Ticket Queue & Details")
    st.caption("Browse, search, and inspect customer support tickets")

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
    col_list, col_detail = st.columns([1, 1.2], gap="large")

    with col_list:
        st.subheader("Ticket List")

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
        st.subheader("Ticket Details")
        ticket = get_ticket_by_id(selected_id)

        if ticket:
            with st.container(border=True):
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.markdown(f"### Ticket #{ticket['id']}")
                with header_col2:
                    st.markdown(f"**:blue-background[{ticket['status'].upper()}]**")

                st.divider()

                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.caption("CUSTOMER")
                    st.markdown(f"**{ticket['customer_name']}**")
                with m_col2:
                    st.caption("SUBMITTED AT")
                    st.markdown(f"{ticket['created_at']}")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                st.caption("SUBJECT")
                st.markdown(f"**{ticket['subject']}**")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                st.caption("DESCRIPTION")
                st.info(ticket["description"], icon="💬")
        else:
            st.error("Selected ticket could not be loaded.")


if __name__ == "__main__" or True:
    render_tickets_page()
