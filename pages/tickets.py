"""
Tickets Queue and Detail View for SupportFlow AI.

Displays all submitted tickets in a structured list with filtering and search,
and provides a dedicated inspection panel for viewing full ticket details
and triggering / displaying AI Ticket Intelligence.
"""

import streamlit as st
import pandas as pd
from services.ticket_service import (
    get_all_tickets,
    get_ticket_by_id,
    get_ticket_analysis,
    analyze_and_store_ticket,
)


def get_priority_color(priority: str) -> str:
    priority_lower = priority.lower()
    if priority_lower == "critical":
        return ":red-background"
    elif priority_lower == "high":
        return ":orange-background"
    elif priority_lower == "medium":
        return ":blue-background"
    return ":gray-background"


def get_sentiment_color(sentiment: str) -> str:
    sentiment_lower = sentiment.lower()
    if sentiment_lower == "positive":
        return ":green-background"
    elif sentiment_lower == "neutral":
        return ":gray-background"
    elif sentiment_lower == "negative":
        return ":orange-background"
    return ":red-background"


def render_tickets_page():
    st.title("Ticket Queue")
    st.caption("Inspect support tickets, triage requests, and review AI analysis")

    tickets = get_all_tickets()

    if not tickets:
        st.info("No tickets found in the database. Use the 'New Ticket' page to create one.")
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
        st.warning("No tickets match the selected filter criteria.")
        return

    # Layout: Split into Table / List and Detail Inspector
    col_list, col_detail = st.columns([1, 1.25], gap="large")

    with col_list:
        st.subheader("Queue")

        ticket_options = {
            f"#{t['id']} — {t['subject'][:35]} ({t['customer_name']})": t["id"]
            for t in filtered_tickets
        }

        selected_label = st.selectbox(
            "Select ticket to view:",
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
            # Customer Ticket Information
            with st.container(border=True):
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.markdown(f"### Ticket #{ticket['id']}")
                with header_col2:
                    status_badge = (
                        f"**:green-background[{ticket['status'].upper()}]**"
                        if ticket["status"] == "AI Analyzed"
                        else f"**:blue-background[{ticket['status'].upper()}]**"
                    )
                    st.markdown(status_badge)

                st.divider()

                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.caption("CUSTOMER")
                    st.markdown(f"**{ticket['customer_name']}**")
                with m_col2:
                    st.caption("SUBMISSION TIMESTAMP")
                    st.markdown(f"{ticket['created_at']}")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                st.caption("SUBJECT")
                st.markdown(f"**{ticket['subject']}**")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                st.caption("DESCRIPTION")
                st.text_area(
                    "Description Text",
                    value=ticket["description"],
                    height=130,
                    disabled=True,
                    label_visibility="collapsed"
                )

            # AI Ticket Analysis Card
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            analysis = get_ticket_analysis(selected_id)

            if analysis:
                with st.container(border=True):
                    ai_hdr1, ai_hdr2 = st.columns([3, 1])
                    with ai_hdr1:
                        st.markdown("#### AI Intelligence")
                    with ai_hdr2:
                        if st.button("Re-analyze", key=f"reanalyze_{selected_id}", use_container_width=True):
                            with st.spinner("Processing analysis..."):
                                ok, res = analyze_and_store_ticket(selected_id)
                                if ok:
                                    st.success("Analysis updated.")
                                    st.rerun()
                                else:
                                    st.error(res)

                    st.divider()

                    m1, m2 = st.columns(2)
                    with m1:
                        st.caption("CATEGORY")
                        st.markdown(f"**{analysis['category']}**")
                    with m2:
                        st.caption("RECOMMENDED DEPARTMENT")
                        st.markdown(f"**{analysis['department']}**")

                    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                    m3, m4 = st.columns(2)
                    with m3:
                        st.caption("PRIORITY")
                        p_color = get_priority_color(analysis["priority"])
                        st.markdown(f"**{p_color}[{analysis['priority'].upper()}]**")
                    with m4:
                        st.caption("SENTIMENT")
                        s_color = get_sentiment_color(analysis["sentiment"])
                        st.markdown(f"**{s_color}[{analysis['sentiment'].upper()}]**")

                    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
                    st.caption("REASONING")
                    st.markdown(f"> {analysis['reasoning']}")
                    st.caption(f"Analyzed at: {analysis['analyzed_at']}")

            else:
                with st.container(border=True):
                    st.markdown("#### AI Intelligence")
                    st.caption("This ticket has not yet been processed by the AI analysis engine.")
                    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                    
                    if st.button("Analyze Ticket", type="primary", key=f"analyze_btn_{selected_id}"):
                        with st.spinner("Processing analysis..."):
                            ok, res = analyze_and_store_ticket(selected_id)
                            if ok:
                                st.success("Ticket analysis complete.")
                                st.rerun()
                            else:
                                st.error(res)

        else:
            st.error("Selected ticket could not be loaded.")


if __name__ == "__main__" or True:
    render_tickets_page()
