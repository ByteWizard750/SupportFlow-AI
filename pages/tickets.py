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


def get_initials(name: str) -> str:
    parts = name.strip().split()
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[1][0]}".upper()


def get_priority_badge(priority: str) -> str:
    p = priority.lower()
    if p == "critical":
        bg, color, border = "rgba(239, 68, 68, 0.15)", "#F87171", "rgba(239, 68, 68, 0.3)"
    elif p == "high":
        bg, color, border = "rgba(245, 158, 11, 0.15)", "#FBBF24", "rgba(245, 158, 11, 0.3)"
    elif p == "medium":
        bg, color, border = "rgba(59, 130, 246, 0.15)", "#60A5FA", "rgba(59, 130, 246, 0.3)"
    else:
        bg, color, border = "rgba(148, 163, 184, 0.15)", "#94A3B8", "rgba(148, 163, 184, 0.3)"
    return f'<span style="background:{bg}; color:{color}; border:1px solid {border}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; letter-spacing:0.04em;">{priority.upper()}</span>'


def get_sentiment_badge(sentiment: str) -> str:
    s = sentiment.lower()
    if s == "positive":
        bg, color, border = "rgba(16, 185, 129, 0.15)", "#34D399", "rgba(16, 185, 129, 0.3)"
    elif s == "neutral":
        bg, color, border = "rgba(148, 163, 184, 0.15)", "#94A3B8", "rgba(148, 163, 184, 0.3)"
    elif s == "negative":
        bg, color, border = "rgba(245, 158, 11, 0.15)", "#FBBF24", "rgba(245, 158, 11, 0.3)"
    else:
        bg, color, border = "rgba(239, 68, 68, 0.15)", "#F87171", "rgba(239, 68, 68, 0.3)"
    return f'<span style="background:{bg}; color:{color}; border:1px solid {border}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; letter-spacing:0.04em;">{sentiment.upper()}</span>'


def get_status_badge(status: str) -> str:
    if status == "AI Analyzed":
        bg, color, border = "rgba(16, 185, 129, 0.15)", "#34D399", "rgba(16, 185, 129, 0.35)"
    else:
        bg, color, border = "rgba(59, 130, 246, 0.15)", "#60A5FA", "rgba(59, 130, 246, 0.35)"
    return f'<span style="background:{bg}; color:{color}; border:1px solid {border}; font-size:11px; font-weight:700; padding:3px 9px; border-radius:4px; letter-spacing:0.06em;">{status.upper()}</span>'


def render_tickets_page():
    # Page Header
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5rem;">
            <div>
                <h1 style="margin: 0; font-size: 1.75rem; font-weight: 700;">Support Queue</h1>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">Triage incoming tickets, review AI intelligence, and inspect grounded knowledge base resolutions</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()

    tickets = get_all_tickets()

    if not tickets:
        st.info("No tickets found in the database. Navigate to 'New Ticket' to create one.")
        return

    # Filter Bar
    filter_col1, filter_col2, filter_col3 = st.columns([3, 1.25, 0.75], gap="small")
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
        st.markdown(
            f"""
            <div style="background: #151C2C; border: 1px solid #1E293B; border-radius: 7px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; color: #94A3B8;">
                {len(tickets)} Total
            </div>
            """,
            unsafe_allow_html=True
        )

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

    # Cockpit Grid: Left Queue Table / Right Inspector
    col_queue, col_detail = st.columns([1, 1.35], gap="medium")

    with col_queue:
        st.markdown(
            """
            <div style="font-size: 0.82rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                Select Ticket
            </div>
            """,
            unsafe_allow_html=True
        )

        ticket_map = {
            f"#{t['id']} — {t['subject'][:32]}... ({t['customer_name']})": t["id"]
            for t in filtered
        }

        selected_key = st.selectbox(
            "Select Ticket",
            options=list(ticket_map.keys()),
            key="ticket_queue_selector",
            label_visibility="collapsed"
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
            use_container_width=True,
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
        initials = get_initials(ticket["customer_name"])

        # Inspector Container
        with st.container(border=True):
            # Customer Header Card
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 4px 0 10px 0;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%); color: white; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; border: 1px solid rgba(255,255,255,0.15);">
                            {initials}
                        </div>
                        <div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC; line-height: 1.3;">
                                #{ticket['id']} — {ticket['subject']}
                            </div>
                            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 2px;">
                                Submitted by <span style="color: #E2E8F0; font-weight: 600;">{ticket['customer_name']}</span> &bull; {ticket['created_at']}
                            </div>
                        </div>
                    </div>
                    <div>
                        {get_status_badge(ticket['status'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Tabbed Workspace
            tab_overview, tab_resolution = st.tabs(["Overview & AI Triage", "Suggested Resolution (RAG)"])

            with tab_overview:
                # Customer Inquiry Body
                st.markdown(
                    """
                    <div style="font-size: 0.78rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px; margin-bottom: 4px;">
                        Customer Inquiry
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.text_area(
                    "Description",
                    value=ticket["description"],
                    height=100,
                    disabled=True,
                    label_visibility="collapsed"
                )

                st.divider()

                # AI Intelligence Header & Actions
                ai_top_left, ai_top_right = st.columns([3, 1.25])
                with ai_top_left:
                    st.markdown(
                        """
                        <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC;">
                            AI Triage Intelligence
                        </div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">
                            Structured ticket classification via Gemini
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
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
                    # 4-Column Metadata Grid
                    st.markdown(
                        f"""
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0 10px 0;">
                            <div style="background: #0F141F; border: 1px solid #1E293B; border-radius: 8px; padding: 10px 14px;">
                                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Category</div>
                                <div style="font-size: 14px; font-weight: 600; color: #F1F5F9; margin-top: 4px;">{analysis['category']}</div>
                            </div>
                            <div style="background: #0F141F; border: 1px solid #1E293B; border-radius: 8px; padding: 10px 14px;">
                                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Assigned Department</div>
                                <div style="font-size: 14px; font-weight: 600; color: #F1F5F9; margin-top: 4px;">{analysis['department']}</div>
                            </div>
                            <div style="background: #0F141F; border: 1px solid #1E293B; border-radius: 8px; padding: 10px 14px;">
                                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">Priority</div>
                                <div>{get_priority_badge(analysis['priority'])}</div>
                            </div>
                            <div style="background: #0F141F; border: 1px solid #1E293B; border-radius: 8px; padding: 10px 14px;">
                                <div style="font-size: 11px; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">Sentiment</div>
                                <div>{get_sentiment_badge(analysis['sentiment'])}</div>
                            </div>
                        </div>
                        <div style="background: rgba(99, 102, 241, 0.05); border: 1px solid rgba(99, 102, 241, 0.25); border-left: 3px solid #6366F1; border-radius: 6px; padding: 10px 14px; margin-top: 10px;">
                            <div style="font-size: 11px; font-weight: 600; color: #818CF8; text-transform: uppercase; letter-spacing: 0.05em;">AI Reasoning</div>
                            <div style="font-size: 13px; color: #E2E8F0; margin-top: 4px; line-height: 1.5;">{analysis['reasoning']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        """
                        <div style="background: #0F141F; border: 1px dashed #334155; border-radius: 8px; padding: 16px; text-align: center; margin: 12px 0;">
                            <div style="font-size: 13px; color: #94A3B8;">This ticket has not yet been processed by the AI analysis engine.</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("Run AI Analysis", type="primary", key=f"analyze_tab_btn_{selected_id}", use_container_width=True):
                        with st.spinner("Analyzing ticket..."):
                            ok, res = analyze_and_store_ticket(selected_id)
                            if ok:
                                st.success("Ticket analyzed.")
                                st.rerun()
                            else:
                                st.error(res)

            with tab_resolution:
                r_top_left, r_top_right = st.columns([3, 1.25])
                with r_top_left:
                    st.markdown(
                        """
                        <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin-top: 4px;">
                            Grounded AI Resolution
                        </div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">
                            Synthesized strictly from indexed internal knowledge base policies
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
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
                    st.markdown(
                        """
                        <div style="font-size: 0.78rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 10px; margin-bottom: 4px;">
                            Draft Resolution (Agent Review Pending)
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.text_area(
                        "Draft Resolution",
                        value=suggested_res["suggested_response"],
                        height=140,
                        disabled=True,
                        label_visibility="collapsed"
                    )

                    # Attributed Sources
                    sources = suggested_res.get("retrieved_sources", [])
                    st.markdown(
                        """
                        <div style="font-size: 0.78rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 10px; margin-bottom: 6px;">
                            Attributed Knowledge Sources
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if sources:
                        source_badges = " ".join([
                            f'<span style="background: #151C2C; border: 1px solid #334155; color: #CBD5E1; font-size: 11px; font-weight: 500; padding: 3px 8px; border-radius: 4px; display: inline-block; margin: 2px 4px 2px 0;">{s}</span>'
                            for s in sources
                        ])
                        st.markdown(source_badges, unsafe_allow_html=True)
                    else:
                        st.caption("No direct policy document matched.")

                    # Matching Chunks Expander
                    if retrieved_chunks:
                        with st.expander(f"Inspect Retrieved Knowledge Context ({len(retrieved_chunks)} Chunks)"):
                            for i, c in enumerate(retrieved_chunks, 1):
                                st.markdown(f"**Chunk {i}: {c.get('doc_title')} — {c.get('section')}** (Cosine Similarity: `{c.get('similarity_score')}`)")
                                st.info(c.get("text", ""))

                    st.caption(f"Drafted at: {suggested_res.get('created_at', '')}")

                else:
                    st.markdown(
                        """
                        <div style="background: #0F141F; border: 1px dashed #334155; border-radius: 8px; padding: 16px; text-align: center; margin: 12px 0;">
                            <div style="font-size: 13px; color: #94A3B8;">Generate a verified customer resolution grounded in internal company documentation.</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if retrieved_chunks:
                        with st.expander(f"Knowledge Context Preview ({len(retrieved_chunks)} matching chunks)"):
                            for i, c in enumerate(retrieved_chunks, 1):
                                st.markdown(f"**{c.get('doc_title')} — {c.get('section')}** (Score: `{c.get('similarity_score')}`)")
                                st.caption(c.get("text")[:180] + "...")

                    if st.button("Generate Suggested Response", type="primary", key=f"gen_tab_btn_{selected_id}", use_container_width=True):
                        with st.spinner("Drafting grounded response..."):
                            ok, res = generate_and_store_response(selected_id)
                            if ok:
                                st.success("Suggested response drafted.")
                                st.rerun()
                            else:
                                st.error(res)


if __name__ == "__main__" or True:
    render_tickets_page()
