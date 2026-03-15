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
    .section-header {
        color: #00C49F;
        font-size: 1.1rem;
        font-weight: 600;
        border-left: 4px solid #00C49F;
        padding-left: 10px;
        margin: 20px 0 10px 0;
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
        # Create directory if it doesn't exist to prevent crash
        os.makedirs("database", exist_ok=True)
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please ensure your DuckDB file is in the database folder.")
        
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

# Data Loading Logic
try:
    (calls_df, agent_df, criteria_df, heatmap_df, qs_df, trans_df, dq_df) = load_data()
    data_ready = True
except Exception as e:
    st.error(f"❌ Connection Error: {e}")
    st.info("Check if 'database/call_quality.duckdb' exists.")
    data_ready = False

# ════════════════════════════════════════════════════════════
# MAIN PAGES
# ════════════════════════════════════════════════════════════
if data_ready:
    if page == "📊 Overview":
        st.header("📊 Call Centre Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Calls", len(calls_df))
        c2.metric("Avg Score", f"{calls_df['overall_score'].mean():.1f}%")
        c3.metric("Agents", agent_df['agent_id'].nunique())
        
        fig_res = px.pie(calls_df, names="resolution", hole=0.4, title="Resolution Breakdown")
        st.plotly_chart(fig_res, use_container_width=True)

    elif page == "👤 Agent Analysis":
        st.header("👤 Agent Performance")
        st.dataframe(agent_df, use_container_width=True, hide_index=True)

    elif page == "📋 Call Explorer":
        st.header("📋 Call Explorer")
        selected_call = st.selectbox("Select Call ID", calls_df["contact_id"].unique())
        
        if selected_call:
            call_row = calls_df[calls_df["contact_id"] == selected_call].iloc[0]
            st.write(f"### Details for Call {selected_call}")
            
            # --- THE FIXED SECTION (Line 733 Logic) ---
            call_scores = qs_df[qs_df["contact_id"] == selected_call]
            if not call_scores.empty:
                st.markdown("#### Quality Criteria Results")
                cols = st.columns(2)
                for idx, (_, sc_row) in enumerate(call_scores.iterrows()):
                    col = cols[idx % 2]
                    icon = "✅" if sc_row["passed"] else "❌"
                    
                    # Using clean, separate lines to prevent SyntaxErrors
                    col.markdown(f"**{icon} {sc_row['criteria_name']}**")
                    col.caption(f"Score: {sc_row['score']*100:.0f}%")
                    col.write(f"Reasoning: {sc_row['reasoning']}")
                    col.markdown("---")

    elif page == "✅ QSDD Quality":
        st.header("✅ Quality Standards")
        fig_crit = px.bar(criteria_df, x="pass_rate", y="criteria_name", orientation='h', color="pass_rate", title="Criteria Pass Rates")
        st.plotly_chart(fig_crit, use_container_width=True)

    elif page == "🤖 AI Chat":
        st.header("🤖 AI Copilot")
        st.info("Integrate your chat_backend.py to enable this feature.")

    elif page == "⚙️ Admin Settings":
        st.header("⚙️ Admin Settings")
        st.write("Framework Configuration coming soon.")

# Footer
st.markdown("---")
st.caption("KrenexAI Call Quality Analyzer | Built with Streamlit & DuckDB")
