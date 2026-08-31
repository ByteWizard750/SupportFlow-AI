"""
Tickets Queue and Detail Inspector for SupportFlow AI.

Full-width stacked cockpit layout:
- Top Section: Header with Stats, Search, Status Filter, Ticket Selector & Overview Queue Table
- Bottom Section: Ticket Details, AI Triage Intelligence, Grounded Resolution & Human Agent Review Workflow
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
from services.agent_service import (
    save_agent_draft,
    mark_in_progress,
    resolve_ticket,
    get_agent_workspace_data,
)


def get_status_badge(status: str) -> str:
    if status == "AI Analyzed":
        return '<span style="background-color: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">AI Analyzed</span>'
    elif status == "In Progress":
        return '<span style="background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">In Progress</span>'
    elif status == "Resolved":
        return '<span style="background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">Resolved</span>'
    return '<span style="background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">New</span>'


def get_priority_badge(priority: str) -> str:
    p = priority.lower()
    if p == "critical":
        color = "#f87171"
        bg = "rgba(239, 68, 68, 0.15)"
        border = "rgba(239, 68, 68, 0.3)"
    elif p == "high":
        color = "#fb923c"
        bg = "rgba(249, 115, 22, 0.15)"
        border = "rgba(249, 115, 22, 0.3)"
    elif p == "medium":
        color = "#60a5fa"
        bg = "rgba(59, 130, 246, 0.15)"
        border = "rgba(59, 130, 246, 0.3)"
    else:
        color = "#9ca3af"
        bg = "rgba(156, 163, 175, 0.15)"
        border = "rgba(156, 163, 175, 0.3)"
    return f'<span style="background-color: {bg}; color: {color}; border: 1px solid {border}; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;">{priority.upper()}</span>'


def get_sentiment_badge(sentiment: str) -> str:
    s = sentiment.lower()
    if s == "positive":
        color = "#4ade80"
        bg = "rgba(34, 197, 94, 0.15)"
        border = "rgba(34, 197, 94, 0.3)"
    elif s == "neutral":
        color = "#9ca3af"
        bg = "rgba(156, 163, 175, 0.15)"
        border = "rgba(156, 163, 175, 0.3)"
    elif s == "negative":
        color = "#fb923c"
        bg = "rgba(249, 115, 22, 0.15)"
        border = "rgba(249, 115, 22, 0.3)"
    else:
        color = "#f87171"
        bg = "rgba(239, 68, 68, 0.15)"
        border = "rgba(239, 68, 68, 0.3)"
    return f'<span style="background-color: {bg}; color: {color}; border: 1px solid {border}; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;">{sentiment.upper()}</span>'


def render_tickets_page():
    tickets = get_all_tickets()
    analyzed_count = sum(1 for t in tickets if t["status"] == "AI Analyzed") if tickets else 0
    resolved_count = sum(1 for t in tickets if t["status"] == "Resolved") if tickets else 0

    # Non-colliding Top Header Row
    st.title("Ticket Queue")
    st.caption("Inspect, triage, review AI suggested responses, and resolve customer support tickets")

    # Clean Inline Counter Badges
    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; margin-top: 4px; margin-bottom: 8px;">
            <span style="background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; color: #94a3b8;">
                Total: <b style="color: #f1f5f9;">{len(tickets)}</b>
            </span>
            <span style="background-color: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.25); border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; color: #4ade80;">
                AI Analyzed: <b>{analyzed_count}</b>
            </span>
            <span style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; color: #34d399;">
                Resolved: <b>{resolved_count}</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    if not tickets:
        st.info("No support tickets found in the database. Navigate to 'New Ticket' to create one.")
        return

    # ==================== TOP SECTION: TICKET QUEUE OVERVIEW ====================
    t_search_col, t_filter_col, t_select_col = st.columns([1.5, 1, 2], gap="medium")

    with t_search_col:
        search_query = st.text_input(
            "Search",
            placeholder="Search by keyword or customer...",
            label_visibility="collapsed"
        )

    with t_filter_col:
        all_possible_statuses = ["All Statuses", "New", "AI Analyzed", "In Progress", "Resolved"]
        selected_status = st.selectbox(
            "Status Filter",
            options=all_possible_statuses,
            label_visibility="collapsed"
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
        st.warning(f"No tickets match the selected filter ('{selected_status}').")
        return

    # Synchronized Ticket Selector Dropdown
    ticket_options = {
        f"#{t['id']} — {t['subject'][:45]}... ({t['customer_name']})": t["id"]
        for t in filtered
    }

    if "active_ticket_id" not in st.session_state or st.session_state["active_ticket_id"] not in [t["id"] for t in filtered]:
        st.session_state["active_ticket_id"] = filtered[0]["id"]

    with t_select_col:
        selected_label = st.selectbox(
            "Select Ticket to Inspect",
            options=list(ticket_options.keys()),
            index=list(ticket_options.values()).index(st.session_state["active_ticket_id"]) if st.session_state["active_ticket_id"] in ticket_options.values() else 0,
            key="ticket_select_dropdown",
            label_visibility="collapsed"
        )
        selected_id = ticket_options[selected_label]
        st.session_state["active_ticket_id"] = selected_id

    # Queue Table across Full Width
    table_rows = []
    for t in filtered:
        table_rows.append({
            "ID": f"#{t['id']}",
            "Customer": t["customer_name"],
            "Subject": t["subject"],
            "Status": t["status"],
            "Submitted": t["created_at"],
        })
    df = pd.DataFrame(table_rows)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=200,
        column_config={
            "ID": st.column_config.TextColumn("ID", width=60),
            "Customer": st.column_config.TextColumn("Customer", width=150),
            "Subject": st.column_config.TextColumn("Subject", width="large"),
            "Status": st.column_config.TextColumn("Status", width=110),
            "Submitted": st.column_config.TextColumn("Submitted", width=160),
        }
    )

    st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)

    # ==================== BOTTOM SECTION: TICKET DETAIL & WORKSPACE ====================
    ticket = get_ticket_by_id(selected_id)
    if not ticket:
        st.error("Selected ticket could not be loaded.")
        return

    analysis = get_ticket_analysis(selected_id)
    suggested_res = get_ticket_suggested_response(selected_id)
    retrieved_chunks = retrieve_ticket_knowledge(selected_id, top_k=3)
    workspace = get_agent_workspace_data(selected_id)

    # Main Detail Workspace Container
    with st.container(border=True):
        # 1. Ticket Header Banner
        h_col1, h_col2 = st.columns([3.8, 1.2])
        with h_col1:
            st.markdown(f"<h3 style='margin: 0 0 2px 0; font-size: 1.25rem;'>Ticket #{ticket['id']}: {ticket['subject']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.82rem; color: #94a3b8;'>Customer: <b style='color: #f1f5f9;'>{ticket['customer_name']}</b> &nbsp;•&nbsp; Submitted: <b>{ticket['created_at']}</b></div>", unsafe_allow_html=True)
        with h_col2:
            st.markdown(f"<div style='text-align: right; padding-top: 4px;'>{get_status_badge(ticket['status'])}</div>", unsafe_allow_html=True)

        st.divider()

        # 2. Customer Inquiry Description
        st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 4px;'>Customer Inquiry</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div style="background-color: rgba(255, 255, 255, 0.025); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 6px; padding: 12px 14px; font-size: 0.9rem; line-height: 1.5; color: #e2e8f0; white-space: pre-wrap;">{ticket['description']}</div>""",
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        # 3. AI Intelligence Triage
        ai_hdr_col1, ai_hdr_col2 = st.columns([4.2, 1])
        with ai_hdr_col1:
            st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase; padding-top: 4px;'>AI Triage Intelligence</div>", unsafe_allow_html=True)
        with ai_hdr_col2:
            if analysis:
                if st.button("Re-analyze", key=f"reanalyze_btn_{selected_id}", use_container_width=True):
                    with st.spinner("Analyzing ticket..."):
                        ok, res = analyze_and_store_ticket(selected_id)
                        if ok:
                            st.success("Analysis updated.")
                            st.rerun()
                        else:
                            st.error(res)

        if analysis:
            st.markdown("<div style='height: 0.15rem;'></div>", unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"<div style='font-size: 0.72rem; color: #94a3b8;'>CATEGORY</div><div style='font-size: 0.9rem; font-weight: 600; color: #f1f5f9;'>{analysis['category']}</div>", unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div style='font-size: 0.72rem; color: #94a3b8;'>DEPARTMENT</div><div style='font-size: 0.9rem; font-weight: 600; color: #f1f5f9;'>{analysis['department']}</div>", unsafe_allow_html=True)
            with m3:
                st.markdown(f"<div style='font-size: 0.72rem; color: #94a3b8;'>PRIORITY</div><div style='margin-top: 2px;'>{get_priority_badge(analysis['priority'])}</div>", unsafe_allow_html=True)
            with m4:
                st.markdown(f"<div style='font-size: 0.72rem; color: #94a3b8;'>SENTIMENT</div><div style='margin-top: 2px;'>{get_sentiment_badge(analysis['sentiment'])}</div>", unsafe_allow_html=True)

            st.markdown("<div style='height: 0.35rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.85rem; color: #cbd5e1; background-color: rgba(255,255,255,0.02); border-left: 3px solid #475569; padding: 8px 12px; border-radius: 0 4px 4px 0;'><b>Reasoning:</b> {analysis['reasoning']}</div>", unsafe_allow_html=True)
        else:
            st.caption("Ticket has not been processed by AI triage engine yet.")
            if st.button("Analyze Ticket with AI", type="primary", key=f"analyze_main_btn_{selected_id}"):
                with st.spinner("Analyzing ticket..."):
                    ok, res = analyze_and_store_ticket(selected_id)
                    if ok:
                        st.success("Ticket analyzed.")
                        st.rerun()
                    else:
                        st.error(res)

        st.divider()

        # 4. Grounded AI Resolution (RAG)
        r_hdr_col1, r_hdr_col2 = st.columns([4.2, 1])
        with r_hdr_col1:
            st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;'>Suggested Resolution (Grounded RAG)</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 0.78rem; color: #64748b;'>Drafted strictly from internal company policy and knowledge base context</div>", unsafe_allow_html=True)
        with r_hdr_col2:
            if suggested_res:
                if st.button("Regenerate", key=f"regen_main_btn_{selected_id}", use_container_width=True):
                    with st.spinner("Regenerating grounded response..."):
                        ok, res = generate_and_store_response(selected_id)
                        if ok:
                            st.success("Resolution refreshed.")
                            st.rerun()
                        else:
                            st.error(res)

        if suggested_res:
            st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
            # Full-Width Resolution Draft Display
            st.markdown(
                f"""<div style="background-color: rgba(30, 41, 59, 0.4); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 6px; padding: 12px 14px; font-size: 0.88rem; line-height: 1.6; color: #f1f5f9; white-space: pre-wrap;">{suggested_res['suggested_response']}</div>""",
                unsafe_allow_html=True
            )

            # Attributed Sources Badges
            sources = suggested_res.get("retrieved_sources", [])
            st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 0.72rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 3px;'>Attributed Knowledge Sources</div>", unsafe_allow_html=True)
            if sources:
                chips_html = " ".join([
                    f'<span style="background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 4px; padding: 2px 7px; font-size: 0.78rem; font-weight: 500; color: #93c5fd; display: inline-block; margin: 2px 4px 4px 0;">{s}</span>'
                    for s in sources
                ])
                st.markdown(chips_html, unsafe_allow_html=True)
            else:
                st.caption("No direct matching knowledge base document found.")

            # Knowledge Chunks Inspector Expander
            if retrieved_chunks:
                st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
                with st.expander(f"Inspect Knowledge Context ({len(retrieved_chunks)} Chunks)"):
                    for i, c in enumerate(retrieved_chunks, 1):
                        st.markdown(f"**Chunk {i}: {c.get('doc_title')} — {c.get('section')}** (Similarity: `{c.get('similarity_score')}`)")
                        st.info(c.get("text", ""))

        else:
            st.markdown("<div style='height: 0.2rem;'></div>", unsafe_allow_html=True)
            st.caption("Generate a resolution draft grounded in internal knowledge base documentation.")

            if retrieved_chunks:
                with st.expander(f"Inspect Knowledge Context ({len(retrieved_chunks)} Chunks)"):
                    for i, c in enumerate(retrieved_chunks, 1):
                        st.markdown(f"**Chunk {i}: {c.get('doc_title')} — {c.get('section')}** (Similarity: `{c.get('similarity_score')}`)")
                        st.caption(c.get("text")[:180] + "...")

            if st.button("Generate Suggested Response", type="primary", key=f"gen_main_btn_{selected_id}"):
                with st.spinner("Drafting grounded response..."):
                    ok, res = generate_and_store_response(selected_id)
                    if ok:
                        st.success("Suggested response drafted.")
                        st.rerun()
                    else:
                        st.error(res)

        st.divider()

        # ==================== 5. HUMAN-IN-THE-LOOP: AGENT REVIEW & RESOLUTION ====================
        st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;'>Agent Review & Resolution</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.78rem; color: #64748b; margin-bottom: 8px;'>Review, edit, and approve the final response before resolving the ticket</div>", unsafe_allow_html=True)

        is_resolved = workspace["is_resolved"]
        resolution_rec = workspace["resolution"]

        # Editable Response Text Area
        agent_edited_text = st.text_area(
            "Agent Final Response",
            value=workspace["initial_text"],
            key=f"agent_text_editor_{selected_id}",
            height=140,
            placeholder="Review, modify, or approve the customer response before resolving...",
            help="Your edited response is preserved separately from the AI suggested draft."
        )

        st.markdown("<div style='height: 0.3rem;'></div>", unsafe_allow_html=True)

        # Action Buttons Row
        act_col1, act_col2, act_col3 = st.columns([1, 1.2, 1.6], gap="small")

        with act_col1:
            if st.button("Save Draft", key=f"save_draft_{selected_id}", use_container_width=True, disabled=is_resolved):
                ok, msg = save_agent_draft(selected_id, agent_edited_text)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with act_col2:
            in_prog_disabled = is_resolved or ticket["status"] == "In Progress"
            if st.button("Mark In Progress", key=f"mark_prog_{selected_id}", use_container_width=True, disabled=in_prog_disabled):
                ok, msg = mark_in_progress(selected_id, agent_edited_text)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with act_col3:
            if st.button("✓ Mark Ticket as Resolved", key=f"mark_resolv_{selected_id}", type="primary", use_container_width=True, disabled=is_resolved):
                ok, msg = resolve_ticket(selected_id, agent_edited_text)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        # Resolution Status Banner if Resolved
        if is_resolved and resolution_rec:
            st.markdown(
                f"""
                <div style="background-color: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 10px 14px; margin-top: 10px; font-size: 0.85rem; color: #6ee7b7;">
                    <b>Ticket Resolved</b> • Resolution approved at {resolution_rec.get('resolved_at', 'Recorded')}
                </div>
                """,
                unsafe_allow_html=True
            )


if __name__ == "__main__" or True:
    render_tickets_page()
