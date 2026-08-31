"""
Support Intelligence Dashboard for SupportFlow AI.

Provides real-time operational metrics, AI triage distributions,
department workload allocations, urgent escalation tracking, deterministic SLA monitoring,
human agent resolution activity, and on-demand executive briefings via Google Gemini.
Polished for enterprise SaaS aesthetics with compact cards and balanced spacing.
"""

import streamlit as st
import pandas as pd
import altair as alt

from services.analytics_service import get_dashboard_analytics, generate_executive_brief
from services.sla_service import get_sla_dashboard_data


def render_category_chart(df: pd.DataFrame):
    """Renders horizontal bar chart for ticket category distribution."""
    if df.empty or df["count"].sum() == 0:
        st.markdown("<div style='color: #64748b; font-size: 0.8rem; padding: 40px 0; text-align: center;'>No category data available yet.</div>", unsafe_allow_html=True)
        return

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, color="#3b82f6")
        .encode(
            x=alt.X("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1, labelFontSize=10, titleFontSize=11)),
            y=alt.Y("category:N", title=None, sort="-x", axis=alt.Axis(labelFontSize=11)),
            tooltip=["category", "count"]
        )
        .properties(height=160)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.04)",
            domainColor="rgba(255, 255, 255, 0.08)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_department_chart(df: pd.DataFrame):
    """Renders horizontal bar chart for department workload to avoid truncated/rotated labels."""
    if df.empty or df["count"].sum() == 0:
        st.markdown("<div style='color: #64748b; font-size: 0.8rem; padding: 40px 0; text-align: center;'>No department workload data available yet.</div>", unsafe_allow_html=True)
        return

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3, color="#8b5cf6")
        .encode(
            x=alt.X("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1, labelFontSize=10, titleFontSize=11)),
            y=alt.Y("department:N", title=None, sort="-x", axis=alt.Axis(labelFontSize=11)),
            tooltip=["department", "count"]
        )
        .properties(height=160)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.04)",
            domainColor="rgba(255, 255, 255, 0.08)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_priority_chart(df: pd.DataFrame):
    """Renders color-coded priority spectrum chart."""
    if df.empty or df["count"].sum() == 0:
        st.markdown("<div style='color: #64748b; font-size: 0.8rem; padding: 40px 0; text-align: center;'>No priority data available yet.</div>", unsafe_allow_html=True)
        return

    color_scale = alt.Scale(
        domain=["Critical", "High", "Medium", "Low"],
        range=["#ef4444", "#f97316", "#3b82f6", "#64748b"]
    )

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
        .encode(
            x=alt.X("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1, labelFontSize=10, titleFontSize=11)),
            y=alt.Y("priority:N", title=None, sort=["Critical", "High", "Medium", "Low"], axis=alt.Axis(labelFontSize=11)),
            color=alt.Color("priority:N", scale=color_scale, legend=None),
            tooltip=["priority", "count"]
        )
        .properties(height=160)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.04)",
            domainColor="rgba(255, 255, 255, 0.08)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_sentiment_chart(df: pd.DataFrame):
    """Renders color-coded customer sentiment pulse chart."""
    if df.empty or df["count"].sum() == 0:
        st.markdown("<div style='color: #64748b; font-size: 0.8rem; padding: 40px 0; text-align: center;'>No sentiment data available yet.</div>", unsafe_allow_html=True)
        return

    color_scale = alt.Scale(
        domain=["Positive", "Neutral", "Negative", "Frustrated"],
        range=["#22c55e", "#64748b", "#f97316", "#ef4444"]
    )

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
        .encode(
            x=alt.X("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1, labelFontSize=10, titleFontSize=11)),
            y=alt.Y("sentiment:N", title=None, sort=["Positive", "Neutral", "Negative", "Frustrated"], axis=alt.Axis(labelFontSize=11)),
            color=alt.Color("sentiment:N", scale=color_scale, legend=None),
            tooltip=["sentiment", "count"]
        )
        .properties(height=160)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.04)",
            domainColor="rgba(255, 255, 255, 0.08)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_sla_distribution_chart(df: pd.DataFrame):
    """Renders color-coded horizontal bar chart for SLA status distribution."""
    if df.empty or df["count"].sum() == 0:
        st.markdown("<div style='color: #64748b; font-size: 0.8rem; padding: 40px 0; text-align: center;'>No SLA records available yet.</div>", unsafe_allow_html=True)
        return

    color_scale = alt.Scale(
        domain=["On Track", "At Risk", "Breached", "Met"],
        range=["#22c55e", "#f59e0b", "#ef4444", "#3b82f6"]
    )

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
        .encode(
            x=alt.X("count:Q", title="Tickets", axis=alt.Axis(tickMinStep=1, labelFontSize=10, titleFontSize=11)),
            y=alt.Y("status:N", title=None, sort=["On Track", "At Risk", "Breached", "Met"], axis=alt.Axis(labelFontSize=11)),
            color=alt.Color("status:N", scale=color_scale, legend=None),
            tooltip=["status", "count"]
        )
        .properties(height=160)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#94a3b8",
            gridColor="rgba(255, 255, 255, 0.04)",
            domainColor="rgba(255, 255, 255, 0.08)"
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_dashboard():
    # 1. Top Header with Clean Inline Status Badge
    st.title("Support Intelligence")
    st.caption("AI-powered operational analytics, deterministic SLA monitoring, and escalation metrics")

    st.markdown(
        """
        <div style="display: flex; gap: 8px; margin-top: 4px; margin-bottom: 8px;">
            <span style="background-color: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.28); border-radius: 6px; padding: 3px 10px; font-size: 0.78rem; color: #4ade80; font-weight: 600; letter-spacing: 0.02em;">
                Live SQL Analytics
            </span>
            <span style="background-color: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.28); border-radius: 6px; padding: 3px 10px; font-size: 0.78rem; color: #93c5fd; font-weight: 600; letter-spacing: 0.02em;">
                SLA Engine Active
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # Load Analytics Data (100% SQL — 0 Gemini calls on page render)
    data = get_dashboard_analytics()
    kpis = data["kpis"]
    sla_data = get_sla_dashboard_data()
    sla_summary = sla_data["summary"]

    # 2. KPI Ribbon (6 Compact Information-Dense Cards in One Row)
    total_val = kpis.get("total_tickets", 0)
    resolved_val = kpis.get("resolved_tickets", 0)
    open_val = kpis.get("open_tickets", max(0, total_val - resolved_val))
    analyzed_val = kpis.get("analyzed_tickets", 0)
    urgent_val = kpis.get("urgent_tickets", 0)
    res_rate_val = kpis.get("resolution_rate_pct", round(resolved_val / total_val * 100.0, 1) if total_val > 0 else 0.0)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6, gap="small")

    with kpi_col1:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">Total Tickets</div>
                <div class="sf-kpi-val">{total_val}</div>
                <div class="sf-kpi-sub">All-time Volume</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">Open Tickets</div>
                <div class="sf-kpi-val">{open_val}</div>
                <div class="sf-kpi-sub">Active Backlog</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">AI Analyzed</div>
                <div class="sf-kpi-val">{analyzed_val}</div>
                <div class="sf-kpi-sub">Triage Ready</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col4:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">Urgent Attention</div>
                <div class="sf-kpi-val" style="color: {'#fb923c' if urgent_val > 0 else '#f8fafc'};">{urgent_val}</div>
                <div class="sf-kpi-sub">High & Critical</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col5:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">Resolved Tickets</div>
                <div class="sf-kpi-val" style="color: {'#34d399' if resolved_val > 0 else '#f8fafc'};">{resolved_val}</div>
                <div class="sf-kpi-sub">Closed by Agents</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi_col6:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">Resolution Rate</div>
                <div class="sf-kpi-val">{res_rate_val}%</div>
                <div class="sf-kpi-sub">Resolution Coverage</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # ==================== 3. SLA & ESCALATION INTELLIGENCE (PHASE 6) ====================
    st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>SLA & Escalation Intelligence</div>", unsafe_allow_html=True)

    sla_kpi1, sla_kpi2, sla_kpi3, sla_kpi4 = st.columns(4, gap="small")

    with sla_kpi1:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">On Track</div>
                <div class="sf-kpi-val" style="color: #4ade80;">{sla_summary['on_track_count']}</div>
                <div class="sf-kpi-sub">Within SLA Window</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with sla_kpi2:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">At Risk</div>
                <div class="sf-kpi-val" style="color: {'#fbbf24' if sla_summary['at_risk_count'] > 0 else '#f8fafc'};">{sla_summary['at_risk_count']}</div>
                <div class="sf-kpi-sub">&ge; 75% SLA Consumed</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with sla_kpi3:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">SLA Breached</div>
                <div class="sf-kpi-val" style="color: {'#f87171' if sla_summary['breached_count'] > 0 else '#f8fafc'};">{sla_summary['breached_count']}</div>
                <div class="sf-kpi-sub">Overdue Deadlines</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with sla_kpi4:
        st.markdown(
            f"""
            <div class="sf-kpi-card">
                <div class="sf-kpi-label">SLA Compliance</div>
                <div class="sf-kpi-val" style="color: {'#34d399' if sla_summary['sla_compliance_rate_pct'] >= 80 else '#fbbf24'};">{sla_summary['sla_compliance_rate_pct']}%</div>
                <div class="sf-kpi-sub">{sla_summary['resolved_within_sla']} of {sla_summary['total_resolved_tickets']} Met</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 0.2rem;'></div>", unsafe_allow_html=True)

    # SLA Charts & Escalation Queue (2 Balanced Columns)
    sla_row_col1, sla_row_col2 = st.columns(2, gap="medium")

    with sla_row_col1:
        with st.container(border=True):
            st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 2px;'>SLA Status Distribution</div>", unsafe_allow_html=True)
            render_sla_distribution_chart(sla_data["df_distribution"])

    with sla_row_col2:
        with st.container(border=True):
            st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 4px;'>🚨 SLA Escalation Queue (At Risk & Breached)</div>", unsafe_allow_html=True)
            esc_queue = sla_data["escalation_queue"]
            if not esc_queue:
                st.markdown("<div style='color: #64748b; font-size: 0.82rem; padding: 40px 0; text-align: center;'>No tickets currently require SLA escalation.</div>", unsafe_allow_html=True)
            else:
                esc_rows = []
                for eq in esc_queue:
                    sla_s = eq.get("sla_status", "On Track")
                    icon = "🔴" if sla_s == "Breached" else "🟡"
                    rem_str = eq.get("formatted_remaining", "N/A")
                    esc_rows.append({
                        "ID": f"#{eq['id']}",
                        "Customer": eq["customer_name"],
                        "Priority": eq.get("priority", "Medium"),
                        "SLA": f"{icon} {sla_s}",
                        "Time Left": rem_str,
                        "Action": eq.get("escalation_recommendation", "Review"),
                    })
                st.dataframe(
                    pd.DataFrame(esc_rows),
                    hide_index=True,
                    use_container_width=True,
                    height=160,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width=45),
                        "Customer": st.column_config.TextColumn("Customer", width=100),
                        "Priority": st.column_config.TextColumn("Priority", width=75),
                        "SLA": st.column_config.TextColumn("SLA Status", width=95),
                        "Time Left": st.column_config.TextColumn("Time Left", width=80),
                        "Action": st.column_config.TextColumn("Escalation Recommendation", width="large"),
                    }
                )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # ==================== 4. AI INTELLIGENCE DISTRIBUTIONS ====================
    st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>AI Intelligence Distributions</div>", unsafe_allow_html=True)

    if not data["has_analysis"]:
        st.info("No tickets have been triaged by the AI engine yet. Analyze tickets in the 'Ticket Queue' to generate distribution analytics.")
    else:
        chart_row1_col1, chart_row1_col2 = st.columns(2, gap="medium")
        with chart_row1_col1:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 2px;'>Category Distribution</div>", unsafe_allow_html=True)
                render_category_chart(data["df_categories"])

        with chart_row1_col2:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 2px;'>Department Workload</div>", unsafe_allow_html=True)
                render_department_chart(data["df_departments"])

        st.markdown("<div style='height: 0.2rem;'></div>", unsafe_allow_html=True)

        chart_row2_col1, chart_row2_col2 = st.columns(2, gap="medium")
        with chart_row2_col1:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 2px;'>Priority Spectrum</div>", unsafe_allow_html=True)
                render_priority_chart(data["df_priorities"])

        with chart_row2_col2:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 2px;'>Customer Sentiment Pulse</div>", unsafe_allow_html=True)
                render_sentiment_chart(data["df_sentiments"])

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # ==================== 5. OPERATIONAL TABLES ====================
    table_col1, table_col2 = st.columns(2, gap="medium")

    with table_col1:
        with st.container(border=True):
            st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 4px;'>Urgent Attention Queue (High / Critical)</div>", unsafe_allow_html=True)
            urgent = data["urgent_tickets"]
            if not urgent:
                st.markdown("<div style='color: #64748b; font-size: 0.82rem; padding: 32px 0; text-align: center;'>No urgent issues detected. All analyzed tickets are routine priority.</div>", unsafe_allow_html=True)
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
                    height=160,
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
            tab_recent, tab_resolutions = st.tabs(["Recent Activity", "Recent Resolutions"])
            
            with tab_recent:
                recent = data["recent_activity"]
                if not recent:
                    st.markdown("<div style='color: #64748b; font-size: 0.82rem; padding: 20px 0; text-align: center;'>No tickets recorded in the database yet.</div>", unsafe_allow_html=True)
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
                        height=140,
                        column_config={
                            "ID": st.column_config.TextColumn("ID", width=45),
                            "Customer": st.column_config.TextColumn("Customer", width=110),
                            "Category": st.column_config.TextColumn("Category", width=130),
                            "Submitted": st.column_config.TextColumn("Submitted", width=135),
                            "Status": st.column_config.TextColumn("Status", width=80),
                        }
                    )

            with tab_resolutions:
                resolutions = data.get("recent_resolutions", [])
                if not resolutions:
                    st.markdown("<div style='color: #64748b; font-size: 0.82rem; padding: 20px 0; text-align: center;'>No tickets marked as Resolved yet.</div>", unsafe_allow_html=True)
                else:
                    res_rows = []
                    for res in resolutions:
                        res_rows.append({
                            "ID": f"#{res['id']}",
                            "Customer": res["customer_name"],
                            "Category": res.get("category", "General"),
                            "Resolved At": res.get("resolved_at", "Completed"),
                            "Status": res["status"],
                        })
                    st.dataframe(
                        pd.DataFrame(res_rows),
                        hide_index=True,
                        use_container_width=True,
                        height=140,
                        column_config={
                            "ID": st.column_config.TextColumn("ID", width=45),
                            "Customer": st.column_config.TextColumn("Customer", width=110),
                            "Category": st.column_config.TextColumn("Category", width=130),
                            "Resolved At": st.column_config.TextColumn("Resolved At", width=135),
                            "Status": st.column_config.TextColumn("Status", width=80),
                        }
                    )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # ==================== 6. EXECUTIVE AI BRIEF ====================
    with st.container(border=True):
        b_hdr_col1, b_hdr_col2 = st.columns([3.8, 1.2])
        with b_hdr_col1:
            st.markdown("<h4 style='margin: 0 0 2px 0; font-size: 1.1rem;'>Executive AI Brief</h4>", unsafe_allow_html=True)
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
                    st.markdown("<div style='font-size: 0.72rem; font-weight: 700; color: #93c5fd; letter-spacing: 0.05em; text-transform: uppercase;'>1. Primary Customer Pain Point</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.85rem; line-height: 1.5; color: #e2e8f0; margin-top: 5px;'>{brief.get('key_pain_point', '')}</div>", unsafe_allow_html=True)

            with b2:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 0.72rem; font-weight: 700; color: #fb923c; letter-spacing: 0.05em; text-transform: uppercase;'>2. Highest Workload / Risk Area</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.85rem; line-height: 1.5; color: #e2e8f0; margin-top: 5px;'>{brief.get('highest_workload_risk', '')}</div>", unsafe_allow_html=True)

            with b3:
                with st.container(border=True):
                    st.markdown("<div style='font-size: 0.72rem; font-weight: 700; color: #4ade80; letter-spacing: 0.05em; text-transform: uppercase;'>3. Recommended Operational Action</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.85rem; line-height: 1.5; color: #e2e8f0; margin-top: 5px;'>{brief.get('recommended_action', '')}</div>", unsafe_allow_html=True)

        else:
            st.markdown("<div style='font-size: 0.85rem; color: #cbd5e1;'>Generate a high-level operational briefing analyzing customer friction points, team workload hotspots, and recommended triage actions.</div>", unsafe_allow_html=True)
            st.markdown("<div style='height: 0.3rem;'></div>", unsafe_allow_html=True)
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
