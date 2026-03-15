# dashboard.py
# Run: python -m streamlit run dashboard.py

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
    page_title="Call Quality Analyzer",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
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
    div[data-testid="stSidebar"] {
        background-color: #1E2130;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ════════════════════════════════════════════════════════════
DB_PATH = "database/call_quality.duckdb"

@st.cache_data(ttl=30)
def load_data():
    """Load all data needed for dashboard — cached for 30s"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
        
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
            SUM(CASE WHEN cs.resolution='Resolved' THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN cs.resolution='Escalated' THEN 1 ELSE 0 END) AS escalated,
            SUM(CASE WHEN cs.resolution='Unresolved' THEN 1 ELSE 0 END) AS unresolved,
            ROUND(AVG(c.total_duration_sec)/60.0, 1)    AS avg_dur_min,
            ROUND(AVG(c.hold_seconds), 0)                AS avg_hold_sec,
            SUM(CASE WHEN c.service_level_flag='1' THEN 1 ELSE 0 END) AS sla_met,
            ROUND(SUM(CASE WHEN cs.sentiment_customer='Positive' THEN 1.0 ELSE 0.0 END)*100.0/NULLIF(COUNT(*),0), 1) AS csat_pct
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

    transcripts_df = con.execute("SELECT * FROM transcripts").fetchdf()

    dq_df = con.execute("""
        SELECT * FROM data_quality_log
        ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
    """).fetchdf()

    con.close()
    return (calls_df, agent_df, criteria_df, heatmap_df, quality_scores_df, transcripts_df, dq_df)

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("KrenexAI")
    st.markdown("---")
    page = st.radio("Navigate", ["📊 Overview", "👤 Agent Analysis", "📋 Call Explorer", "✅ QSDD Quality", "🤖 AI Chat", "⚙️ Admin Settings"])
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Data Loading
try:
    (calls_df, agent_df, criteria_df, heatmap_df, qs_df, trans_df, dq_df) = load_data()
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

COLORS = {"green": "#00C49F", "yellow": "#FFBB28", "orange": "#FF8042", "red": "#FF4444", "blue": "#0088FE", "bg": "#1E2130"}

# ════════════════════════════════════════════════════════════
# PAGES (Condensed Logic)
# ════════════════════════════════════════════════════════════

if page == "📊 Overview":
    st.header("📊 Call Centre Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Calls", len(calls_df))
    c2.metric("Avg Score", f"{calls_df['overall_score'].mean():.1f}%")
    c3.metric("Agents", agent_df['agent_id'].nunique())
    
    fig_res = px.pie(calls_df, names="resolution", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_res)

elif page == "👤 Agent Analysis":
    st.header("👤 Agent Performance")
    st.dataframe(agent_df, use_container_width=True)

elif page == "📋 Call Explorer":
    st.header("📋 Call Explorer")
    selected_call = st.selectbox("Select Call ID", calls_df["contact_id"].unique())
    
    if selected_call:
        call_row = calls_df[calls_df["contact_id"] == selected_call].iloc[0]
        st.write(f"### Details for Call {selected_call}")
        
        # FIX FOR LINE 733 (The original error)
        call_scores = qs_df[qs_df["contact_id"] == selected_call]
        if not call_scores.empty:
            cols = st.columns(2)
            for idx, (_, sc_row) in enumerate(call_scores.iterrows()):
                col = cols[idx % 2]
                icon = "✅" if sc_row["passed"] else "❌"
                # Corrected string handling
                col.markdown(f"**{icon} {sc_row['criteria_name']}**")
                col.caption(f"Score: {sc_row['score']*100:.0f}% | Reasoning: {sc_row['reasoning']}")

elif page == "✅ QSDD Quality":
    st.header("✅ Quality Standards")
    fig_crit = px.bar(criteria_df, x="pass_rate", y="criteria_name", orientation='h', color="pass_rate")
    st.plotly_chart(fig_crit)

elif page == "🤖 AI Chat":
    st.header("🤖 AI Copilot")
    st.info("Chat backend connection required.")

elif page == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.write("Manage Quality Framework")

# Footer
st.markdown("---")
st.caption("KrenexAI Call Quality Analyzer v1.0")
