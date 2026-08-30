"""
Tickets Queue and Detail View for SupportFlow AI.

Displays all submitted tickets in a structured list with filtering and search,
and provides a dedicated inspection panel with tabbed navigation for:
- Ticket Overview & AI Intelligence
- Grounded Suggested Resolution (RAG)
"""

import streamlit as st
import pandas as pd
from services.ticket_service import (
    get_all_tickets,
    get_ticket_by_id,
    get_ticket_analysis,
    analyze_and_store_ticket,
    retrieve_ticket_knowledge,
    generate_and_store_response,
    get_ticket_suggested_response,
)


def get_priority_badge(priority: str) -> str:
    p_lower = priority.lower()
    if p_lower == "critical":
        return ":red-background[CRITICAL]"
    elif p_lower == "high":
        return ":orange-background[HIGH]"
    elif p_lower == "medium":
        return ":blue-background[MEDIUM]"
    return ":gray-background[LOW]"


def get_sentiment_badge(sentiment: str) -> str:
    s_lower = sentiment.lower()
    if s_lower == "positive":
        return ":green-background[POSITIVE]"
    elif s_lower == "neutral":
        return ":gray-background[NEUTRAL]"
    elif s_lower == "negative":
        return ":orange-background[NEGATIVE]"
    return ":red-background[FRUSTRATED]"


def render_tickets_page():
    # Page Header
    st.title("Ticket Queue")
    st.caption("Browse, triage, and inspect customer tickets with AI intelligence and grounded knowledge base resolutions")
    st.divider()

    tickets = get_all_tickets()

    if not tickets:
        st.info("No tickets found in the database. Navigate to 'New Ticket' to create one.")
        return

    # Filter Bar
    filter_col1, filter_col2, filter_col3 = st.columns([3, 1.5, 1])
    with filter_col1:
        search_query = st.text_input(
            "Search",
            placeholder="Search by ticket ID, customer name, or keywords...",
            label_visibility="collapsed"
        )
    with filter_col2:
        status_options = ["All Statuses"] + sorted(list({t["status"] for t in tickets}))
        selected_status = st.selectbox(
            "Status",
            options=status_options,
            label_visibility="collapsed"
        )
    with filter_col3:
        st.caption(f"**{len(tickets)} total**")

    # Filter Logic
    filtered = tickets
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            t for t in filtered
            if q in str(t["id"]).lower()
            or q in t["customer_name"].lower()
            or q in t["subject"].lower()
            or q in t["description"].lower()
        ]

    if selected_status != "All Statuses":
        filtered = [t for t in filtered if t["status"] == selected_status]

    if not filtered:
        st.warning("No tickets match the search criteria.")
        return

    # Two-Column Cockpit Layout
    col_queue, col_detail = st.columns([1.1, 1.4], gap="medium")

    with col_queue:
        st.subheader("Queue")

        ticket_map = {
            f"#{t['id']} — {t['subject'][:32]}... ({t['customer_name']})": t["id"]
            for t in filtered
        }

        selected_key = st.selectbox(
            "Select Ticket to Inspect",
            options=list(ticket_map.keys()),
            key="ticket_queue_selector"
        )
        selected_id = ticket_map[selected_key]

        # Compact Overview Table
        table_rows = []
        for t in filtered:
            table_rows.append({
                "ID": f"#{t['id']}",
                "Customer": t["customer_name"],
                "Subject": t["subject"],
                "Status": t["status"],
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
            }
        )

    with col_detail:
        ticket = get_ticket_by_id(selected_id)
        if not ticket:
            st.error("Selected ticket could not be loaded.")
            return

        analysis = get_ticket_analysis(selected_id)
        suggested_res = get_ticket_suggested_response(selected_id)
        retrieved_chunks = retrieve_ticket_knowledge(selected_id, top_k=3)

        # Header Bar inside bordered card
        with st.container(border=True):
            # Ticket Header Row
            hdr_left, hdr_right = st.columns([3, 1.2])
            with hdr_left:
                st.subheader(f"Ticket #{ticket['id']}: {ticket['subject']}")
                st.caption(f"Submitted by **{ticket['customer_name']}** on {ticket['created_at']}")
            with hdr_right:
                status_color = ":green-background" if ticket["status"] == "AI Analyzed" else ":blue-background"
                st.markdown(f"**{status_color}[{ticket['status'].upper()}]**")

            # Tabs for Clean Inspection
            tab_overview, tab_resolution = st.tabs(["Overview & AI Triage", "Suggested Resolution (RAG)"])

            with tab_overview:
                # Customer Description
                st.caption("CUSTOMER INQUIRY")
                st.text_area(
                    "Description",
                    value=ticket["description"],
                    height=100,
                    disabled=True,
                    label_visibility="collapsed"
                )

                st.divider()

                # AI Intelligence Sub-section
                ai_top_left, ai_top_right = st.columns([3, 1.2])
                with ai_top_left:
                    st.markdown("##### AI Triage Intelligence")
                with ai_top_right:
                    if analysis:
                        if st.button("Re-analyze", key=f"reanalyze_tab_{selected_id}", use_container_width=True):
                            with st.spinner("Analyzing..."):
                                ok, res = analyze_and_store_ticket(selected_id)
                                if ok:
                                    st.success("Analysis refreshed.")
                                    st.rerun()
                                else:
                                    st.error(res)

                if analysis:
                    m1, m2 = st.columns(2)
                    with m1:
                        st.caption("CATEGORY")
                        st.markdown(f"**{analysis['category']}**")
                    with m2:
                        st.caption("RECOMMENDED DEPARTMENT")
                        st.markdown(f"**{analysis['department']}**")

                    m3, m4 = st.columns(2)
                    with m3:
                        st.caption("PRIORITY")
                        st.markdown(f"**{get_priority_badge(analysis['priority'])}**")
                    with m4:
                        st.caption("SENTIMENT")
                        st.markdown(f"**{get_sentiment_badge(analysis['sentiment'])}**")

                    st.caption("REASONING")
                    st.markdown(f"> {analysis['reasoning']}")
                else:
                    st.caption("This ticket has not been classified by the AI engine yet.")
                    if st.button("Analyze Ticket with AI", type="primary", key=f"analyze_tab_btn_{selected_id}"):
                        with st.spinner("Analyzing ticket..."):
                            ok, res = analyze_and_store_ticket(selected_id)
                            if ok:
                                st.success("Ticket analyzed.")
                                st.rerun()
                            else:
                                st.error(res)

            with tab_resolution:
                r_top_left, r_top_right = st.columns([3, 1.2])
                with r_top_left:
                    st.markdown("##### Grounded AI Resolution")
                    st.caption("Generated strictly from company knowledge base documentation")
                with r_top_right:
                    if suggested_res:
                        if st.button("Regenerate", key=f"regen_tab_{selected_id}", use_container_width=True):
                            with st.spinner("Regenerating response..."):
                                ok, res = generate_and_store_response(selected_id)
                                if ok:
                                    st.success("Response updated.")
                                    st.rerun()
                                else:
                                    st.error(res)

                if suggested_res:
                    st.caption("DRAFT RESPONSE (PENDING AGENT APPROVAL)")
                    st.text_area(
                        "Draft Resolution",
                        value=suggested_res["suggested_response"],
                        height=140,
                        disabled=True,
                        label_visibility="collapsed"
                    )

                    # Attributed Sources
                    sources = suggested_res.get("retrieved_sources", [])
                    st.caption("ATTRIBUTED KNOWLEDGE SOURCES")
                    if sources:
                        for s in sources:
                            st.markdown(f"- `:gray-background[{s}]`")
                    else:
                        st.caption("No direct policy document matched.")

                    # Matching Chunks Expander
                    if retrieved_chunks:
                        with st.expander(f"Inspect Knowledge Context ({len(retrieved_chunks)} Chunks)"):
                            for i, c in enumerate(retrieved_chunks, 1):
                                st.markdown(f"**{c.get('doc_title')} — {c.get('section')}** (Score: `{c.get('similarity_score')}`)")
                                st.info(c.get("text", ""))

                    st.caption(f"Drafted at: {suggested_res.get('created_at', '')}")

                else:
                    st.caption("Generate a resolution draft grounded in internal knowledge base documentation.")
                    
                    if retrieved_chunks:
                        with st.expander(f"Knowledge Context Preview ({len(retrieved_chunks)} matching chunks)"):
                            for i, c in enumerate(retrieved_chunks, 1):
                                st.markdown(f"**{c.get('doc_title')} — {c.get('section')}** (Score: `{c.get('similarity_score')}`)")
                                st.caption(c.get("text")[:180] + "...")

                    if st.button("Generate Suggested Response", type="primary", key=f"gen_tab_btn_{selected_id}"):
                        with st.spinner("Drafting grounded response..."):
                            ok, res = generate_and_store_response(selected_id)
                            if ok:
                                st.success("Suggested response drafted.")
                                st.rerun()
                            else:
                                st.error(res)


if __name__ == "__main__" or True:
    render_tickets_page()
