"""
Support Intelligence Dashboard for SupportFlow AI.

Provides real-time operational metrics, AI triage distributions,
department workload allocations, urgent escalation tracking,
and on-demand executive briefings via Google Gemini.
"""

import streamlit as st
import pandas as pd
import altair as alt

from services.analytics_service import get_dashboard_analytics, generate_executive_brief


def render_category_chart(df: pd.DataFrame):
    """Renders horizontal bar chart for ticket category distribution."""
    if df.empty:
        st.info("No category data available yet.")
        return

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#3b82f6")
        .encode(
            x=alt.X("count:Q", title="Ticket Count", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("category:N", title=None, sort="-x"),
            tooltip=["category", "count"]
        )
        .properties(height=230)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.06)",
            domainColor="rgba(255, 255, 255, 0.1)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_department_chart(df: pd.DataFrame):
    """Renders bar chart for department workload."""
    if df.empty:
        st.info("No department workload data available yet.")
        return

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#8b5cf6")
        .encode(
            x=alt.X("department:N", title=None, axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("count:Q", title="Assigned Tickets", axis=alt.Axis(tickMinStep=1)),
            tooltip=["department", "count"]
        )
        .properties(height=230)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.06)",
            domainColor="rgba(255, 255, 255, 0.1)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_priority_chart(df: pd.DataFrame):
    """Renders color-coded priority spectrum bar chart."""
    if df.empty:
        st.info("No priority data available yet.")
        return

    color_scale = alt.Scale(
        domain=["Critical", "High", "Medium", "Low"],
        range=["#ef4444", "#f97316", "#3b82f6", "#64748b"]
    )

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("priority:N", title=None, sort=["Critical", "High", "Medium", "Low"]),
            y=alt.Y("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("priority:N", scale=color_scale, legend=None),
            tooltip=["priority", "count"]
        )
        .properties(height=230)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.06)",
            domainColor="rgba(255, 255, 255, 0.1)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_sentiment_chart(df: pd.DataFrame):
    """Renders color-coded customer sentiment pulse chart."""
    if df.empty:
        st.info("No sentiment data available yet.")
        return

    color_scale = alt.Scale(
        domain=["Positive", "Neutral", "Negative", "Frustrated"],
        range=["#22c55e", "#64748b", "#f97316", "#ef4444"]
    )

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("sentiment:N", title=None, sort=["Positive", "Neutral", "Negative", "Frustrated"]),
            y=alt.Y("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("sentiment:N", scale=color_scale, legend=None),
            tooltip=["sentiment", "count"]
        )
        .properties(height=230)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.06)",
            domainColor="rgba(255, 255, 255, 0.1)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_dashboard():
    # 1. Top Header
    hdr_left, hdr_right = st.columns([3, 1.2])
    with hdr_left:
        st.title("Support Intelligence")
        st.caption("AI-powered operational analytics and workload triage for your support workflow")
    with hdr_right:
        st.markdown(
            """
            <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%; padding-top: 14px;">
                <span style="background-color: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.25); border-radius: 6px; padding: 4px 12px; font-size: 0.8rem; color: #4ade80; font-weight: 500;">
                    Live SQL Analytics
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # Load Analytics Data (100% SQL — 0 Gemini calls)
    data = get_dashboard_analytics()
    kpis = data["kpis"]

    # 2. KPI Ribbon (5 Compact Cards)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        with st.container(border=True):
            st.metric(
                label="Total Tickets",
                value=kpis["total_tickets"],
                help="Total volume of tickets registered in SQLite"
            )
            st.caption("All-time Volume")

    with kpi_col2:
        with st.container(border=True):
            st.metric(
                label="Pending Triage",
                value=kpis["new_tickets"],
                help="Tickets in 'New' status awaiting triage"
            )
            st.caption("Status: New")

    with kpi_col3:
        with st.container(border=True):
            st.metric(
                label="AI Analyzed",
                value=kpis["analyzed_tickets"],
                help="Tickets successfully triaged by Gemini"
            )
            st.caption(f"{kpis['triage_coverage_pct']}% Coverage")

    with kpi_col4:
        with st.container(border=True):
            st.metric(
                label="Urgent Attention",
                value=kpis["urgent_tickets"],
                help="Tickets assigned High or Critical priority"
            )
            st.caption("High & Critical")

    with kpi_col5:
        with st.container(border=True):
            st.metric(
                label="Grounded Responses",
                value=f"{kpis['rag_coverage_pct']}%",
                help="Percentage of tickets with RAG suggested responses generated"
            )
            st.caption(f"{kpis['rag_responses']} Drafts Ready")

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # 3. AI Intelligence Analytics Grid (2 x 2 Balanced Charts)
    st.markdown("#### AI Intelligence Distributions")

    if not data["has_analysis"]:
        st.info("No tickets have been triaged by the AI engine yet. Analyze tickets in the 'Ticket Queue' to generate distribution analytics.")
    else:
        chart_row1_col1, chart_row1_col2 = st.columns(2, gap="medium")
        with chart_row1_col1:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;'>Category Distribution</div>", unsafe_allow_html=True)
                render_category_chart(data["df_categories"])

        with chart_row1_col2:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;'>Department Workload</div>", unsafe_allow_html=True)
                render_department_chart(data["df_departments"])

        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)

        chart_row2_col1, chart_row2_col2 = st.columns(2, gap="medium")
        with chart_row2_col1:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;'>Priority Spectrum</div>", unsafe_allow_html=True)
                render_priority_chart(data["df_priorities"])

        with chart_row2_col2:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;'>Customer Sentiment Pulse</div>", unsafe_allow_html=True)
                render_sentiment_chart(data["df_sentiments"])

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # 4. Workload & Operational Tables (2 Balanced Columns)
    table_col1, table_col2 = st.columns(2, gap="medium")

    with table_col1:
        with st.container(border=True):
            st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;'>Urgent Attention Queue (High / Critical)</div>", unsafe_allow_html=True)
            urgent = data["urgent_tickets"]
            if not urgent:
                st.markdown("<div style='color: #64748b; font-size: 0.85rem; padding: 24px 0; text-align: center;'>No urgent issues detected. All analyzed tickets are routine priority.</div>", unsafe_allow_html=True)
            else:
                urgent_rows = []
                for u in urgent:
                    urgent_rows.append({
                        "ID": f"#{u['id']}",
                        "Customer": u["customer_name"],
                        "Category": u.get("category", "General"),
                        "Priority": u["priority"],
                        "Status": u["status"],
                    })
                st.dataframe(
                    pd.DataFrame(urgent_rows),
                    hide_index=True,
                    use_container_width=True,
                    height=200,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width=45),
                        "Customer": st.column_config.TextColumn("Customer", width=110),
                        "Category": st.column_config.TextColumn("Category", width=140),
                        "Priority": st.column_config.TextColumn("Priority", width=80),
                        "Status": st.column_config.TextColumn("Status", width=85),
                    }
                )

    with table_col2:
        with st.container(border=True):
            st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;'>Recent Ticket Activity</div>", unsafe_allow_html=True)
            recent = data["recent_activity"]
            if not recent:
                st.markdown("<div style='color: #64748b; font-size: 0.85rem; padding: 24px 0; text-align: center;'>No tickets recorded in the database yet.</div>", unsafe_allow_html=True)
            else:
                recent_rows = []
                for r in recent:
                    recent_rows.append({
                        "ID": f"#{r['id']}",
                        "Customer": r["customer_name"],
                        "Category": r.get("category", "Pending"),
                        "Submitted": r["created_at"],
                        "Status": r["status"],
                    })
                st.dataframe(
                    pd.DataFrame(recent_rows),
                    hide_index=True,
                    use_container_width=True,
                    height=200,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width=45),
                        "Customer": st.column_config.TextColumn("Customer", width=110),
                        "Category": st.column_config.TextColumn("Category", width=130),
                        "Submitted": st.column_config.TextColumn("Submitted", width=135),
                        "Status": st.column_config.TextColumn("Status", width=80),
                    }
                )

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # 5. On-Demand Executive AI Brief (Gemini synthesis only on explicit user click)
    with st.container(border=True):
        b_hdr_col1, b_hdr_col2 = st.columns([3.8, 1.2])
        with b_hdr_col1:
            st.markdown("<h4 style='margin: 0 0 2px 0;'>Executive AI Brief</h4>", unsafe_allow_html=True)
            st.caption("On-demand operational intelligence synthesized by Gemini based on current support data")
        with b_hdr_col2:
            if "executive_ai_brief" in st.session_state and st.session_state["executive_ai_brief"]:
                if st.button("Regenerate Brief", key="regen_brief_btn", use_container_width=True):
                    with st.spinner("Synthesizing support intelligence brief..."):
                        ok, result = generate_executive_brief(
                            kpis=kpis,
                            recent_tickets=data["recent_activity"],
                            categories=data["categories"],
                            urgent_tickets=data["urgent_tickets"]
                        )
                        if ok:
                            st.session_state["executive_ai_brief"] = result
                            st.success("Executive brief refreshed.")
                            st.rerun()
                        else:
                            st.error(result)

        st.divider()

        if "executive_ai_brief" in st.session_state and st.session_state["executive_ai_brief"]:
            brief = st.session_state["executive_ai_brief"]
            
            b1, b2, b3 = st.columns(3, gap="medium")
            with b1:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #93c5fd; letter-spacing: 0.05em; text-transform: uppercase;'>1. Primary Customer Pain Point</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.88rem; line-height: 1.5; color: #e2e8f0; margin-top: 6px;'>{brief.get('key_pain_point', '')}</div>", unsafe_allow_html=True)

            with b2:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #fb923c; letter-spacing: 0.05em; text-transform: uppercase;'>2. Highest Workload / Risk Area</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.88rem; line-height: 1.5; color: #e2e8f0; margin-top: 6px;'>{brief.get('highest_workload_risk', '')}</div>", unsafe_allow_html=True)

            with b3:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #4ade80; letter-spacing: 0.05em; text-transform: uppercase;'>3. Recommended Operational Action</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.88rem; line-height: 1.5; color: #e2e8f0; margin-top: 6px;'>{brief.get('recommended_action', '')}</div>", unsafe_allow_html=True)

        else:
            st.markdown("Generate a high-level operational briefing analyzing customer friction points, team workload hotspots, and recommended triage actions.")
            st.markdown("<div style='height: 0.2rem;'></div>", unsafe_allow_html=True)
            if st.button("Generate Executive AI Brief", type="primary", key="gen_brief_btn"):
                with st.spinner("Synthesizing support intelligence brief with Gemini..."):
                    ok, result = generate_executive_brief(
                        kpis=kpis,
                        recent_tickets=data["recent_activity"],
                        categories=data["categories"],
                        urgent_tickets=data["urgent_tickets"]
                    )
                    if ok:
                        st.session_state["executive_ai_brief"] = result
                        st.success("Executive brief generated successfully.")
                        st.rerun()
                    else:
                        st.error(result)


if __name__ == "__main__" or True:
    render_dashboard()
