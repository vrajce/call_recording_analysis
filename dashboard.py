
# dashboard.py
# Run: streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import duckdb
import joblib
import os
import warnings
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title  = "Call Quality Analyzer",
    page_icon   = "📞",
    layout      = "wide",
    initial_sidebar_state = "expanded"
)

# Dark theme CSS
st.markdown("""
<style>
    .main { background-color: #0F1117; }
    .stMetric {
        background-color: #1E2130;
        border: 1px solid #2D3250;
        border-radius: 10px;
        padding: 15px;
    }
    .metric-card {
        background: #1E2130;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2D3250;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #AAAAAA;
        margin: 0;
    }
    .section-header {
        color: #00C49F;
        font-size: 1.1rem;
        font-weight: 600;
        border-left: 4px solid #00C49F;
        padding-left: 10px;
        margin: 20px 0 10px 0;
    }
    .call-card {
        background: #1E2130;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        border-left: 4px solid #0088FE;
    }
    .badge-resolved   { background:#00C49F22; color:#00C49F;
                        border:1px solid #00C49F; border-radius:20px;
                        padding:2px 10px; font-size:0.8rem; }
    .badge-escalated  { background:#FFBB2822; color:#FFBB28;
                        border:1px solid #FFBB28; border-radius:20px;
                        padding:2px 10px; font-size:0.8rem; }
    .badge-unresolved { background:#FF444422; color:#FF4444;
                        border:1px solid #FF4444; border-radius:20px;
                        padding:2px 10px; font-size:0.8rem; }
    div[data-testid="stSidebar"] {
        background-color: #1E2130;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ════════════════════════════════════════════════════════════
DB_PATH = "database/call_quality.duckdb"

@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

@st.cache_data(ttl=30)
def load_data():
    """Load all data needed for dashboard — cached for 30s"""
    con = duckdb.connect(DB_PATH, read_only=True)

    calls_df = con.execute("""
        SELECT c.*, cs.overall_score, cs.resolution,
               cs.sentiment_agent, cs.sentiment_customer,
               cs.issue_category, cs.ai_recommendation,
               cs.pred_issue_category, cs.pred_resolution,
               cs.key_moments
        FROM calls c
        JOIN call_summary cs ON c.contact_id = cs.contact_id
    """).fetchdf()

    agent_df = con.execute("""
        SELECT
            c.agent_id, c.team_name, c.skill_name,
            COUNT(DISTINCT c.contact_id)                AS total_calls,
            ROUND(AVG(cs.overall_score), 1)             AS avg_score,
            ROUND(MAX(cs.overall_score), 1)             AS best_score,
            ROUND(MIN(cs.overall_score), 1)             AS worst_score,
            SUM(CASE WHEN cs.resolution="Resolved"
                     THEN 1 ELSE 0 END)                 AS resolved,
            SUM(CASE WHEN cs.resolution="Escalated"
                     THEN 1 ELSE 0 END)                 AS escalated,
            SUM(CASE WHEN cs.resolution="Unresolved"
                     THEN 1 ELSE 0 END)                 AS unresolved,
            ROUND(AVG(c.total_duration_sec)/60.0, 1)    AS avg_dur_min,
            ROUND(AVG(c.hold_seconds), 0)               AS avg_hold_sec,
            SUM(CASE WHEN c.service_level_flag="1"
                     THEN 1 ELSE 0 END)                 AS sla_met,
            ROUND(SUM(CASE WHEN cs.sentiment_customer="Positive"
                           THEN 1.0 ELSE 0.0 END)*100.0/
                  NULLIF(COUNT(*),0), 1)                AS csat_pct
        FROM calls c
        JOIN call_summary cs ON c.contact_id = cs.contact_id
        GROUP BY c.agent_id, c.team_name, c.skill_name
        ORDER BY avg_score DESC
    """).fetchdf()

    criteria_df = con.execute("""
        SELECT criteria_name, section_name,
               ROUND(AVG(CASE WHEN passed THEN 100.0 ELSE 0.0 END),1) AS pass_rate,
               COUNT(*) AS total
        FROM quality_scores
        GROUP BY criteria_name, section_name
        ORDER BY pass_rate ASC
    """).fetchdf()

    heatmap_df = con.execute("""
        SELECT qs.agent_id, qs.criteria_name,
               ROUND(AVG(CASE WHEN qs.passed THEN 100.0 ELSE 0.0 END),1) AS pass_rate
        FROM quality_scores qs
        GROUP BY qs.agent_id, qs.criteria_name
    """).fetchdf()

    quality_scores_df = con.execute("""
        SELECT qs.*, c.agent_id AS ag_id, c.team_name
        FROM quality_scores qs
        JOIN calls c ON qs.contact_id = c.contact_id
    """).fetchdf()

    transcripts_df = con.execute("""
        SELECT contact_id,
               LEFT(agent_text, 500)    AS agent_preview,
               LEFT(customer_text, 300) AS customer_preview,
               agent_word_count, customer_word_count, talk_ratio
        FROM transcripts
    """).fetchdf()

    dq_df = con.execute("""
        SELECT * FROM data_quality_log
        ORDER BY CASE severity
            WHEN "high" THEN 1 WHEN "medium" THEN 2 ELSE 3 END
    """).fetchdf()

    con.close()
    return (calls_df, agent_df, criteria_df,
            heatmap_df, quality_scores_df,
            transcripts_df, dq_df)

# ════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1E2130/00C49F?text=KrenexAI",
             use_column_width=True)
    st.markdown("---")
    st.markdown("### 📞 Call Quality Analyzer")
    st.markdown("*AI-Powered Analytics*")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["📊 Overview",
         "👤 Agent Analysis",
         "📋 Call Explorer",
         "✅ QSDD Quality",
         "🤖 AI Chat",
         "⚙️ Admin Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### 🔄 Data Status")

    # Live counter
    try:
        con_check = duckdb.connect(DB_PATH, read_only=True)
        n_calls   = con_check.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
        n_real    = con_check.execute("SELECT COUNT(*) FROM calls WHERE is_simulated=false").fetchone()[0]
        n_sim     = con_check.execute("SELECT COUNT(*) FROM calls WHERE is_simulated=true").fetchone()[0]
        con_check.close()
        st.metric("Total Calls",     n_calls)
        st.metric("Real Calls",      n_real)
        st.metric("Simulated Calls", n_sim)
    except:
        st.warning("DB not connected")

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Load all data
try:
    (calls_df, agent_df, criteria_df,
     heatmap_df, qs_df, trans_df, dq_df) = load_data()
    data_loaded = True
except Exception as e:
    st.error(f"❌ Cannot connect to database: {e}")
    st.info("Make sure database/call_quality.duckdb exists")
    data_loaded = False
    st.stop()

# ════════════════════════════════════════════════════════════
# COLOUR HELPERS
# ════════════════════════════════════════════════════════════
COLORS = {
    "green":  "#00C49F", "yellow": "#FFBB28",
    "orange": "#FF8042", "red":    "#FF4444",
    "blue":   "#0088FE", "purple": "#8884D8",
    "teal":   "#00BCD4", "bg":     "#1E2130",
}

def score_color(s):
    if s >= 80: return COLORS["green"]
    if s >= 60: return COLORS["yellow"]
    if s >= 40: return COLORS["orange"]
    return COLORS["red"]

def score_emoji(s):
    if s >= 80: return "🟢"
    if s >= 60: return "🟡"
    if s >= 40: return "🟠"
    return "🔴"

PLOTLY_LAYOUT = dict(
    paper_bgcolor = "#0F1117",
    plot_bgcolor  = "#1E2130",
    font_color    = "#FFFFFF",
    font_size     = 12,
    margin        = dict(l=20, r=20, t=40, b=20),
    legend        = dict(bgcolor="#1E2130", bordercolor="#2D3250"),
    xaxis         = dict(gridcolor="#2D3250", zerolinecolor="#2D3250"),
    yaxis         = dict(gridcolor="#2D3250", zerolinecolor="#2D3250"),
)

# ════════════════════════════════════════════════════════════
# PAGE 1: OVERVIEW
# ════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown("# 📊 Call Centre Overview")
    st.markdown("*Real-time analytics across all calls and agents*")
    st.markdown("---")

    # ── KPI Row 1 ────────────────────────────────────────────
    total   = len(calls_df)
    avg_sc  = calls_df["overall_score"].mean().round(1)
    aban    = calls_df["is_abandoned"].sum()
    agents  = calls_df["agent_id"].nunique()
    sla_met = (calls_df["service_level_flag"]=="1").sum()
    resolved= (calls_df["resolution"]=="Resolved").sum()

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("📞 Total Calls",   total)
    c2.metric("⭐ Avg Score",     f"{avg_sc}%",
              delta=f"{'↑ Good' if avg_sc>=60 else '↓ Needs work'}")
    c3.metric("👤 Active Agents", agents)
    c4.metric("✅ SLA Met",
              f"{sla_met/total*100:.0f}%",
              delta=f"{sla_met}/{total}")
    c5.metric("📵 Abandoned",
              f"{aban/total*100:.0f}%",
              delta=f"{aban} calls",
              delta_color="inverse")
    c6.metric("🎯 Resolved",
              f"{resolved/total*100:.0f}%",
              delta=f"{resolved}/{total}")

    st.markdown("---")

    # ── Row 1: Score Distribution + Resolution ─────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-header">Quality Score Distribution</p>',
                    unsafe_allow_html=True)
        calls_df["grade"] = calls_df["overall_score"].apply(
            lambda s: "Excellent (80-100)" if s>=80 else
                      "Good (60-79)"       if s>=60 else
                      "Average (40-59)"    if s>=40 else
                      "Poor (0-39)"
        )
        grade_counts = calls_df["grade"].value_counts().reset_index()
        grade_counts.columns = ["grade","count"]
        fig_pie = px.pie(
            grade_counts, values="count", names="grade",
            color="grade",
            color_discrete_map={
                "Excellent (80-100)": COLORS["green"],
                "Good (60-79)":       COLORS["yellow"],
                "Average (40-59)":    COLORS["orange"],
                "Poor (0-39)":        COLORS["red"],
            },
            hole=0.55
        )
        fig_pie.update_layout(**PLOTLY_LAYOUT, showlegend=True)
        fig_pie.update_traces(textposition="outside",
                               textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown('<p class="section-header">Resolution Outcomes (ML Model 2)</p>',
                    unsafe_allow_html=True)
        res_counts = calls_df["resolution"].value_counts().reset_index()
        res_counts.columns = ["resolution","count"]
        fig_res = px.bar(
            res_counts, x="resolution", y="count",
            color="resolution",
            color_discrete_map={
                "Resolved":   COLORS["green"],
                "Escalated":  COLORS["yellow"],
                "Unresolved": COLORS["red"],
                "Abandoned":  "#888888",
            },
            text="count"
        )
        fig_res.update_traces(textposition="outside")
        fig_res.update_layout(**PLOTLY_LAYOUT,
                               showlegend=False,
                               xaxis_title="Resolution",
                               yaxis_title="Calls")
        st.plotly_chart(fig_res, use_container_width=True)

    # ── Row 2: Issue Categories + Score by Team ─────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<p class="section-header">Issue Categories (ML Model 1 — Auto-tagged)</p>',
                    unsafe_allow_html=True)
        issue_data = calls_df.groupby("issue_category").agg(
            count=("contact_id","count"),
            avg_score=("overall_score","mean")
        ).reset_index()
        issue_data["avg_score"] = issue_data["avg_score"].round(1)

        fig_issue = make_subplots(specs=[[{"secondary_y": True}]])
        fig_issue.add_trace(
            go.Bar(x=issue_data["issue_category"],
                   y=issue_data["count"],
                   name="Calls",
                   marker_color=COLORS["blue"],
                   text=issue_data["count"],
                   textposition="outside"),
            secondary_y=False
        )
        fig_issue.add_trace(
            go.Scatter(x=issue_data["issue_category"],
                       y=issue_data["avg_score"],
                       mode="lines+markers",
                       name="Avg Score %",
                       line=dict(color=COLORS["green"], width=3),
                       marker=dict(size=10)),
            secondary_y=True
        )
        fig_issue.update_layout(**PLOTLY_LAYOUT, showlegend=True)
        fig_issue.update_yaxes(title_text="Calls",     secondary_y=False)
        fig_issue.update_yaxes(title_text="Avg Score", secondary_y=True,
                                range=[0,110])
        st.plotly_chart(fig_issue, use_container_width=True)

    with col4:
        st.markdown('<p class="section-header">Score Distribution by Team</p>',
                    unsafe_allow_html=True)
        team_data = calls_df.groupby("team_name").agg(
            avg_score=("overall_score","mean"),
            calls=("contact_id","count")
        ).reset_index().sort_values("avg_score", ascending=False)
        team_data["avg_score"] = team_data["avg_score"].round(1)
        team_data["color"] = team_data["avg_score"].apply(score_color)

        fig_team = px.bar(
            team_data, x="avg_score", y="team_name",
            orientation="h",
            color="avg_score",
            color_continuous_scale=["#FF4444","#FFBB28","#00C49F"],
            range_color=[0,100],
            text="avg_score",
            hover_data=["calls"]
        )
        fig_team.update_traces(texttemplate="%{text:.1f}%",
                                textposition="outside")
        fig_team.add_vline(x=75, line_dash="dash",
                            line_color=COLORS["green"],
                            annotation_text="Target 75%")
        fig_team.update_layout(**PLOTLY_LAYOUT,
                                showlegend=False,
                                xaxis_title="Avg Score %",
                                yaxis_title="",
                                xaxis_range=[0,110])
        st.plotly_chart(fig_team, use_container_width=True)

    # ── Data Quality Summary ─────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-header">⚠️ Data Quality Log</p>',
                unsafe_allow_html=True)

    if len(dq_df) > 0:
        sev_map = {"high":"🔴 High","medium":"🟡 Medium","low":"🟢 Low"}
        dq_df["sev_label"] = dq_df["severity"].map(sev_map)
        st.dataframe(
            dq_df[["sev_label","field_name","issue_type",
                   "issue_description","logged_at"]].rename(columns={
                "sev_label":"Severity","field_name":"Field",
                "issue_type":"Type","issue_description":"Description",
                "logged_at":"Logged At"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No data quality issues found!")


# ════════════════════════════════════════════════════════════
# PAGE 2: AGENT ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "👤 Agent Analysis":
    st.markdown("# 👤 Agent Performance Analysis")
    st.markdown("*Individual agent metrics, rankings and coaching insights*")
    st.markdown("---")

    # ── Agent Leaderboard ────────────────────────────────────
    st.markdown('<p class="section-header">Agent Leaderboard</p>',
                unsafe_allow_html=True)

    agent_df_disp = agent_df.copy()
    agent_df_disp["Grade"] = agent_df_disp["avg_score"].apply(
        lambda s: "🟢 Excellent" if s>=75 else
                  "🟡 Good"      if s>=60 else
                  "🟠 Average"   if s>=40 else
                  "🔴 Poor"
    )
    agent_df_disp["SLA %"] = (
        agent_df_disp["sla_met"] /
        agent_df_disp["total_calls"] * 100
    ).round(1)

    st.dataframe(
        agent_df_disp[[
            "agent_id","team_name","total_calls","avg_score",
            "Grade","resolved","escalated","unresolved",
            "avg_dur_min","avg_hold_sec","SLA %","csat_pct"
        ]].rename(columns={
            "agent_id":"Agent ID","team_name":"Team",
            "total_calls":"Calls","avg_score":"Avg Score %",
            "resolved":"Resolved","escalated":"Escalated",
            "unresolved":"Unresolved","avg_dur_min":"Avg Dur (min)",
            "avg_hold_sec":"Avg Hold (s)","csat_pct":"CSAT %"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-header">Score Comparison — All Agents</p>',
                    unsafe_allow_html=True)
        fig_lb = px.bar(
            agent_df.sort_values("avg_score"),
            x="avg_score", y="agent_id",
            orientation="h",
            color="avg_score",
            color_continuous_scale=["#FF4444","#FFBB28","#00C49F"],
            range_color=[0,100],
            text="avg_score",
            hover_data=["team_name","total_calls"]
        )
        fig_lb.update_traces(texttemplate="%{text:.1f}%",
                              textposition="outside")
        fig_lb.add_vline(x=75, line_dash="dash",
                          line_color=COLORS["green"],
                          annotation_text="Target")
        fig_lb.update_layout(**PLOTLY_LAYOUT,
                              showlegend=False,
                              xaxis_range=[0,115],
                              xaxis_title="Avg Score %",
                              yaxis_title="Agent ID",
                              yaxis_type="category")
        st.plotly_chart(fig_lb, use_container_width=True)

    with col2:
        st.markdown('<p class="section-header">Call Volume & Resolution per Agent</p>',
                    unsafe_allow_html=True)
        fig_stacked = px.bar(
            agent_df.sort_values("total_calls", ascending=False),
            x="agent_id",
            y=["resolved","escalated","unresolved"],
            color_discrete_map={
                "resolved":   COLORS["green"],
                "escalated":  COLORS["yellow"],
                "unresolved": COLORS["red"],
            },
            barmode="stack",
            text_auto=True
        )
        fig_stacked.update_layout(**PLOTLY_LAYOUT,
                                   xaxis_title="Agent ID",
                                   yaxis_title="Calls",
                                   xaxis_type="category",
                                   legend_title="Resolution")
        st.plotly_chart(fig_stacked, use_container_width=True)

    # ── Strengths & Weaknesses Heatmap ───────────────────────
    st.markdown("---")
    st.markdown('<p class="section-header">Strengths & Weaknesses Heatmap — Agent × QSDD Criteria</p>',
                unsafe_allow_html=True)
    st.caption("Green = Strong ✅  |  Red = Needs Training ❌")

    pivot = heatmap_df.pivot_table(
        index="agent_id",
        columns="criteria_name",
        values="pass_rate",
        fill_value=0
    )
    fig_heat = px.imshow(
        pivot,
        color_continuous_scale=["#FF4444","#FFBB28","#00C49F"],
        range_color=[0,100],
        text_auto=True,
        aspect="auto"
    )
    fig_heat.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="QSDD Criteria",
        yaxis_title="Agent ID",
        coloraxis_colorbar_title="Pass %"
    )
    fig_heat.update_traces(textfont_size=9)
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── Individual Agent Drilldown ────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-header">Individual Agent Report</p>',
                unsafe_allow_html=True)

    selected_agent = st.selectbox(
        "Select Agent",
        options=agent_df["agent_id"].tolist(),
        format_func=lambda x:
            f"Agent {x} — " +
            agent_df[agent_df["agent_id"]==x]["team_name"].values[0]
    )

    if selected_agent:
        ag_row = agent_df[agent_df["agent_id"]==selected_agent].iloc[0]
        ag_score = float(ag_row["avg_score"])

        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Calls",       int(ag_row["total_calls"]))
        m2.metric("Avg Score",   f"{ag_score:.1f}%",
                  delta=f"{'↑ Good' if ag_score>=60 else '↓ Below target'}")
        m3.metric("Resolved",    int(ag_row["resolved"]))
        m4.metric("Avg Duration",f"{ag_row['avg_dur_min']} min")
        m5.metric("CSAT",        f"{ag_row['csat_pct']:.0f}%")

        # Agent criteria radar
        ag_crit = heatmap_df[heatmap_df["agent_id"]==selected_agent]
        if len(ag_crit) > 0:
            fig_radar = go.Figure(go.Scatterpolar(
                r    = ag_crit["pass_rate"].tolist() +
                       [ag_crit["pass_rate"].iloc[0]],
                theta= ag_crit["criteria_name"].tolist() +
                       [ag_crit["criteria_name"].iloc[0]],
                fill = "toself",
                line_color = score_color(ag_score),
                fillcolor  = score_color(ag_score) + "33",
                name  = f"Agent {selected_agent}"
            ))
            fig_radar.update_layout(
                **PLOTLY_LAYOUT,
                polar=dict(
                    bgcolor=COLORS["bg"],
                    radialaxis=dict(visible=True, range=[0,100],
                                    gridcolor="#2D3250",
                                    tickfont_color="#AAAAAA"),
                    angularaxis=dict(gridcolor="#2D3250",
                                     tickfont_color="#FFFFFF")
                ),
                title=f"Agent {selected_agent} — QSDD Radar Chart"
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Top 3 strengths and weaknesses
        s_col, w_col = st.columns(2)
        with s_col:
            st.markdown("**💪 Top 3 Strengths:**")
            top3 = ag_crit.nlargest(3,"pass_rate")
            for _, r in top3.iterrows():
                st.success(f"✅ {r['criteria_name']} — {r['pass_rate']:.0f}%")

        with w_col:
            st.markdown("**⚠️ Top 3 Needs Training:**")
            bot3 = ag_crit.nsmallest(3,"pass_rate")
            for _, r in bot3.iterrows():
                st.error(f"❌ {r['criteria_name']} — {r['pass_rate']:.0f}%")


# ════════════════════════════════════════════════════════════
# PAGE 3: CALL EXPLORER
# ════════════════════════════════════════════════════════════
elif page == "📋 Call Explorer":
    st.markdown("# 📋 Call Explorer")
    st.markdown("*Browse all calls — filter, search, inspect*")
    st.markdown("---")

    # ── Filters ──────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        filter_res = st.multiselect(
            "Resolution",
            options=calls_df["resolution"].unique().tolist(),
            default=calls_df["resolution"].unique().tolist()
        )
    with fc2:
        filter_issue = st.multiselect(
            "Issue Category",
            options=calls_df["issue_category"].dropna().unique().tolist(),
            default=calls_df["issue_category"].dropna().unique().tolist()
        )
    with fc3:
        filter_team = st.multiselect(
            "Team",
            options=calls_df["team_name"].unique().tolist(),
            default=calls_df["team_name"].unique().tolist()
        )
    with fc4:
        score_range = st.slider(
            "Quality Score Range",
            min_value=0, max_value=100,
            value=(0, 100)
        )

    # Apply filters
    filtered = calls_df[
        (calls_df["resolution"].isin(filter_res)) &
        (calls_df["issue_category"].isin(filter_issue)) &
        (calls_df["team_name"].isin(filter_team)) &
        (calls_df["overall_score"] >= score_range[0]) &
        (calls_df["overall_score"] <= score_range[1])
    ]

    st.markdown(f"**Showing {len(filtered)} of {len(calls_df)} calls**")
    st.markdown("---")

    # ── Call Table ────────────────────────────────────────────
    disp_cols = [
        "contact_id","agent_id","team_name",
        "overall_score","resolution","issue_category",
        "pred_issue_category","pred_resolution",
        "total_duration_sec","is_abandoned","is_simulated"
    ]
    available = [c for c in disp_cols if c in filtered.columns]

    st.dataframe(
        filtered[available].rename(columns={
            "contact_id":"Call ID","agent_id":"Agent",
            "team_name":"Team","overall_score":"Score %",
            "resolution":"Resolution","issue_category":"Issue",
            "pred_issue_category":"ML Issue",
            "pred_resolution":"ML Resolution",
            "total_duration_sec":"Duration (s)",
            "is_abandoned":"Abandoned","is_simulated":"Simulated"
        }).sort_values("Score %"),
        use_container_width=True,
        hide_index=True
    )

    # ── Individual Call Drilldown ─────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-header">Call Detail View</p>',
                unsafe_allow_html=True)

    selected_call = st.selectbox(
        "Select Call to Inspect",
        options=filtered["contact_id"].tolist(),
        format_func=lambda x: (
            f"Call {x} | Score: " +
            str(filtered[filtered["contact_id"]==x]["overall_score"].values[0]) +
            "% | " +
            str(filtered[filtered["contact_id"]==x]["resolution"].values[0])
        )
    )

    if selected_call:
        call_row  = filtered[filtered["contact_id"]==selected_call].iloc[0]
        trans_row = trans_df[trans_df["contact_id"]==selected_call]

        sc = float(call_row["overall_score"])
        d1,d2,d3,d4,d5 = st.columns(5)
        d1.metric("Quality Score", f"{sc:.1f}%")
        d2.metric("Resolution",     call_row["resolution"])
        d3.metric("Issue",          call_row["issue_category"])
        d4.metric("ML Prediction",  str(call_row.get("pred_resolution","N/A")))
        d5.metric("Duration",
                  f"{call_row['total_duration_sec']/60:.1f} min")

        # Criteria scores for this call
        call_scores = qs_df[qs_df["contact_id"]==selected_call]
        if len(call_scores) > 0:
            st.markdown("**QSDD Scores for this call:**")
            cs_cols = st.columns(4)
            for idx, (_, sc_row) in enumerate(call_scores.iterrows()):
                col = cs_cols[idx % 4]
                icon = "✅" if sc_row["passed"] else "❌"
                col.markdown(
                    f"**{icon} {sc_row['criteria_name']}**  
"
                    f"{sc_row['score']*100:.0f}%  
"
                    f"*{sc_row['reasoning'][:60]}...*"
                    if len(str(sc_row["reasoning"]))>60
                    else f"*{sc_row['reasoning']}*"
                )

        # Transcript
        if len(trans_row) > 0:
            st.markdown("---")
            t1, t2 = st.columns(2)
            with t1:
                st.markdown("**🎧 Agent Said:**")
                st.info(trans_row["agent_preview"].values[0])
            with t2:
                st.markdown("**👤 Customer Said:**")
                st.warning(trans_row["customer_preview"].values[0])

            wc1, wc2, wc3 = st.columns(3)
            wc1.metric("Agent Words",
                        int(trans_row["agent_word_count"].values[0]))
            wc2.metric("Customer Words",
                        int(trans_row["customer_word_count"].values[0]))
            wc3.metric("Agent Talk Ratio",
                        f"{float(trans_row['talk_ratio'].values[0])*100:.0f}%")

        # AI Recommendation
        if call_row.get("ai_recommendation"):
            st.markdown("---")
            st.markdown("**🤖 AI Coaching Recommendation:**")
            st.info(call_row["ai_recommendation"])


# ════════════════════════════════════════════════════════════
# PAGE 4: QSDD QUALITY
# ════════════════════════════════════════════════════════════
elif page == "✅ QSDD Quality":
    st.markdown("# ✅ QSDD Quality Analysis")
    st.markdown("*How well agents follow the quality standard guidelines*")
    st.markdown("---")

    # ── Overall criteria pass rates ──────────────────────────
    st.markdown('<p class="section-header">Criteria Pass Rates — Weakest to Strongest</p>',
                unsafe_allow_html=True)

    fig_crit = px.bar(
        criteria_df.sort_values("pass_rate"),
        x="pass_rate", y="criteria_name",
        orientation="h",
        color="pass_rate",
        color_continuous_scale=["#FF4444","#FFBB28","#00C49F"],
        range_color=[0,100],
        text="pass_rate",
        hover_data=["section_name","total"]
    )
    fig_crit.update_traces(texttemplate="%{text:.0f}%",
                            textposition="outside")
    fig_crit.add_vline(x=75, line_dash="dash",
                        line_color=COLORS["green"],
                        annotation_text="Target 75%")
    fig_crit.add_vline(x=50, line_dash="dot",
                        line_color=COLORS["orange"],
                        annotation_text="Warning 50%")
    fig_crit.update_layout(**PLOTLY_LAYOUT,
                            showlegend=False,
                            xaxis_range=[0,115],
                            xaxis_title="Pass Rate %",
                            yaxis_title="",
                            height=500)
    st.plotly_chart(fig_crit, use_container_width=True)

    # ── Section scores ────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-header">Score by QSDD Section</p>',
                    unsafe_allow_html=True)
        sec_data = criteria_df.groupby("section_name").agg(
            avg_pass=("pass_rate","mean")
        ).reset_index()
        sec_data["avg_pass"] = sec_data["avg_pass"].round(1)
        sec_data["short"] = sec_data["section_name"].str.replace(
            "Section ","Sec ").str[:20]

        fig_sec = px.bar(
            sec_data, x="short", y="avg_pass",
            color="avg_pass",
            color_continuous_scale=["#FF4444","#FFBB28","#00C49F"],
            range_color=[0,100],
            text="avg_pass"
        )
        fig_sec.update_traces(texttemplate="%{text:.0f}%",
                               textposition="outside")
        fig_sec.add_hline(y=75, line_dash="dash",
                           line_color=COLORS["green"])
        fig_sec.update_layout(**PLOTLY_LAYOUT,
                               showlegend=False,
                               yaxis_range=[0,110],
                               xaxis_title="Section",
                               yaxis_title="Avg Pass Rate %")
        st.plotly_chart(fig_sec, use_container_width=True)

    with col2:
        st.markdown('<p class="section-header">Criteria Detail Table</p>',
                    unsafe_allow_html=True)
        criteria_display = criteria_df.copy()
        criteria_display["Status"] = criteria_display["pass_rate"].apply(
            lambda v: "✅ Good" if v>=75 else
                      "⚠️ Warning" if v>=50 else
                      "❌ Critical"
        )
        st.dataframe(
            criteria_display[[
                "criteria_name","section_name",
                "pass_rate","total","Status"
            ]].rename(columns={
                "criteria_name":"Criteria",
                "section_name":"Section",
                "pass_rate":"Pass Rate %",
                "total":"Total Calls"
            }),
            use_container_width=True,
            hide_index=True
        )

    # ── Critical criteria alert ───────────────────────────────
    st.markdown("---")
    critical = criteria_df[criteria_df["pass_rate"] < 50]
    if len(critical) > 0:
        st.error(f"🚨 **{len(critical)} criteria below 50% pass rate — urgent coaching needed!**")
        for _, r in critical.iterrows():
            st.error(f"❌ **{r['criteria_name']}** ({r['section_name']}) — "
                     f"Only {r['pass_rate']:.0f}% of agents pass this")
    else:
        st.success("✅ All criteria above 50% pass rate!")


# ════════════════════════════════════════════════════════════
# PAGE 5: AI CHAT (friend's RAG chatbot)
# ════════════════════════════════════════════════════════════
elif page == "🤖 AI Chat":
    st.markdown("# 🤖 AI Manager Copilot")
    st.markdown("*Ask anything about your calls in plain English*")
    st.markdown("---")

    try:
        from chat_backend import get_answer
        chat_available = True
    except ImportError:
        chat_available = False

    if not chat_available:
        st.warning("""
        **RAG Chatbot not connected.**

        To enable: make sure `chat_backend.py` is in the same folder
        and run: `python generate_ai_summary_overwrite_hf.py` first.
        """)

        st.markdown("**Example questions you can ask once connected:**")
        examples = [
            "Which agents have the lowest quality scores?",
            "Show me calls where the agent failed the greeting",
            "What are the most common customer issues?",
            "Which calls were unresolved today?",
            "Summarize call 626398259531",
            "Which agent handles billing issues best?",
        ]
        for ex in examples:
            if st.button(f"💬 {ex}"):
                st.info(f"Question: {ex}\n\nConnect chat_backend.py to get answers!")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about your calls..."):
            st.session_state.messages.append(
                {"role":"user","content":prompt}
            )
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing calls..."):
                    response = get_answer(prompt)
                    st.markdown(response)
                st.session_state.messages.append(
                    {"role":"assistant","content":response}
                )


# ════════════════════════════════════════════════════════════
# PAGE 6: ADMIN SETTINGS (friend's QSDD CRUD)
# ════════════════════════════════════════════════════════════
elif page == "⚙️ Admin Settings":
    st.markdown("# ⚙️ QSDD Admin Settings")
    st.markdown("*Manage quality scoring rules — no code required*")
    st.markdown("---")

    try:
        from tools.qsdd_admin import (
            get_all_rules, add_rule,
            update_rule, delete_rule
        )
        admin_available = True
    except ImportError:
        admin_available = False

    if not admin_available:
        # Fallback: show rules from DB directly
        st.warning("Admin module not fully connected — showing read-only view")

    con_admin = duckdb.connect(DB_PATH)
    rules_df  = con_admin.execute("""
        SELECT framework_id, section_name, criteria_name,
               ROUND(effective_weight*100,1) AS weight_pct,
               enabled, scoring_method,
               what_to_check, when_to_check
        FROM qsdd_framework
        ORDER BY section_name, criteria_name
    """).fetchdf()
    con_admin.close()

    st.markdown(f"**{len(rules_df)} active quality rules**")
    st.dataframe(
        rules_df.rename(columns={
            "framework_id":"ID","section_name":"Section",
            "criteria_name":"Criteria","weight_pct":"Weight %",
            "enabled":"Active","scoring_method":"Scoring",
            "what_to_check":"What to Check",
            "when_to_check":"When"
        }),
        use_container_width=True,
        hide_index=True
    )

    if admin_available:
        st.markdown("---")
        st.markdown('<p class="section-header">Manage Rules</p>',
                    unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["➕ Add Rule","✏️ Update Rule","🗑️ Delete Rule"])

        with tab1:
            with st.form("add_rule"):
                a1,a2 = st.columns(2)
                section  = a1.text_input("Section Name")
                criteria = a2.text_input("Criteria Name")
                b1,b2,b3 = st.columns(3)
                sw      = b1.number_input("Section Weight", 0.0,1.0,0.25)
                cw      = b2.number_input("Criteria Weight",0.0,1.0,0.25)
                enabled = b3.checkbox("Enabled", value=True)
                what    = st.text_area("What to Check")
                when    = st.text_input("When")
                method  = st.selectbox("Scoring",
                            ["binary","llm_evaluated"])
                if st.form_submit_button("➕ Add Rule"):
                    add_rule(section,criteria,sw,cw,
                             enabled,what,when,method)
                    st.success("✅ Rule added!")
                    st.rerun()

        with tab2:
            rule_id = st.selectbox("Select Rule to Update",
                                    rules_df["ID"].tolist())
            field   = st.selectbox("Field to Update",
                        ["enabled","what_to_check",
                         "criteria_weight","section_weight"])
            value   = st.text_input("New Value")
            if st.button("✏️ Update"):
                update_rule(rule_id, field, value)
                st.success("✅ Updated!")
                st.rerun()

        with tab3:
            del_id = st.selectbox("Select Rule to Delete",
                                   rules_df["ID"].tolist())
            if st.button("🗑️ Delete", type="primary"):
                delete_rule(del_id)
                st.success("✅ Deleted!")
                st.rerun()


# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<center style='color:#444;font-size:0.8rem;'>"
    "AI-Powered Call Quality Analyzer | KrenexAI Hackathon | "
    "Built with Streamlit + DuckDB + Plotly"
    "</center>",
    unsafe_allow_html=True
)
