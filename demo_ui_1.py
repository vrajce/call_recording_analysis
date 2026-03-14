import streamlit as st
import pandas as pd
import plotly.express as px  # ADD THIS IMPORT

# --- Page Config ---
st.set_page_config(page_title="KenexAI Quality Analyzer", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Persona Dashboard:", 
                        ["Manager Dashboard", "Agent Dashboard", "Admin Settings (QSDD)"])

# --- 1. MANAGER DASHBOARD ---
if page == "Manager Dashboard":
    st.title("Manager Analytics & AI Copilot")
    
    # 1. KPI Cards 
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Calls Analyzed", "1,402", "12 today")
    col2.metric("Average Quality Score", "82%", "Up 4%")
    col3.metric("Missing Transcripts", "3", "-1")
    col4.metric("Top Issue Category", "Hardware", "BitLocker")
    
    st.divider()
    
    # 2. VISUAL ANALYTICS SECTION (The Upgrade)
    st.subheader("Visibility at Scale")
    chart_col1, chart_col2, chart_col3 = st.columns(3)
    
    # Mock Data for Charts (Your Data Engineer will feed real SQL data here)
    trend_data = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri"], "Score": [75, 78, 77, 82, 85]})
    issue_data = pd.DataFrame({"Category": ["Hardware", "Billing", "Login", "Other"], "Calls": [450, 320, 210, 150]})
    agent_data = pd.DataFrame({"Agent": ["Priya", "Rahul", "David", "Amit"], "Avg Score": [95, 88, 74, 65]}).sort_values("Avg Score", ascending=True)

    with chart_col1:
        fig_trend = px.line(trend_data, x="Day", y="Score", title="Average Quality Score (7 Days)", markers=True)
        fig_trend.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_trend, use_container_width=True)

    with chart_col2:
        fig_issues = px.bar(issue_data, x="Category", y="Calls", title="Call Volume by Issue Category", color="Category")
        fig_issues.update_layout(height=300, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_issues, use_container_width=True)

    with chart_col3:
        fig_agents = px.bar(agent_data, x="Avg Score", y="Agent", orientation='h', title="Agent Leaderboard")
        fig_agents.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_agents, use_container_width=True)

    st.divider()
    
    # 3. SPLIT VIEW: Call Log/Deep-Dive vs. AI Copilot
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("Call Deep-Dive")
        # Mock Data representing your Fact Table
        mock_data = pd.DataFrame({
            "Call ID": ["626189712437", "626189712438", "626189712439"],
            "Agent": ["David Clark", "Priya Singh", "Rahul Sharma"],
            "Duration (s)": [2776, 320, 845],
            "Score": ["72%", "95%", "60%"],
            "Category": ["Hardware", "Billing", "Login"]
        })
        st.dataframe(mock_data, use_container_width=True, hide_index=True)
        
        selected_call = st.selectbox("Select a Call ID to view AI Analysis:", mock_data["Call ID"])
        
        if selected_call == "626189712437":
            st.info("**AI Summary:** Customer Lucas Scott called regarding a BitLocker blue screen error and insufficient C-Drive space. Agent David Clark attempted to transfer files to OneDrive and successfully pinned the necessary folders to Quick Access.")
            st.success("**Strengths:** Agent was patient and properly authenticated the user's name and location.")
            st.warning("**Improvements:** Agent failed to collect a callback number in case of disconnection.")

    with right_col:
        st.subheader("AI Manager Copilot")
        st.markdown("Chat with your database for instant insights.")
        
        # Streamlit Chat Interface
        messages = st.container(height=350)
        messages.chat_message("assistant").write("Hello! I notice a spike in Hardware calls today. What would you like to investigate?")
        
        if prompt := st.chat_input("e.g., Why are David's scores dropping?"):
            messages.chat_message("user").write(prompt)
            messages.chat_message("assistant").write(f"Analyzing data for: '{prompt}'... (Your LangChain SQL Agent will reply here)")

# --- (Keep Agent Dashboard and Admin Settings below this exactly as they were) ---