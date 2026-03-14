import streamlit as st
import pandas as pd
import plotly.express as px
from chat_backend import ask_hybrid

# --- Page Config ---
st.set_page_config(page_title="KenexAI Quality Analyzer", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Persona Dashboard:",
    ["Manager Dashboard", "AI Copilot (Full Screen)", "Agent Dashboard", "Admin Settings (QSDD)"],
)
debug_tool = st.sidebar.checkbox("Debug: Show tool choice", value=False)

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
    
    # 2. VISUAL ANALYTICS SECTION
    st.subheader("Visibility at Scale")
    chart_col1, chart_col2, chart_col3 = st.columns(3)
    
    # Mock Data for Charts
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
        st.markdown("Chat with your transcripts for instant insights.")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Add initial assistant message
            st.session_state.messages.append({"role": "assistant", "content": "Hello! I notice a spike in Hardware calls today. What would you like to investigate?"})
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("🔍 See Sources (Call IDs)"):
                        for source_id in message["sources"]:
                            st.write(f"- Call ID: {source_id}")
        
        # Chat input
        if prompt := st.chat_input("e.g., Why are customers calling about blue screens?"):
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            # Append user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get response from AI
            with st.chat_message("assistant"):
                with st.spinner("Searching transcripts via Nebius AI..."):
                    result = ask_hybrid(prompt)
                    response = result.get("answer", "")
                    sources = result.get("sources", [])
                    tool_used = result.get("tool", "")
                    
                    st.markdown(response)
                    if debug_tool and tool_used:
                        st.caption(f"Tool: {tool_used.upper()}")
                    
                    # Add sources in an expander for verification
                    if sources:
                        with st.expander("🔍 See Sources (Call IDs)"):
                            for source_id in set(sources):
                                st.write(f"- Call ID: {source_id}")
            
            # Append assistant message to history (including sources for re-rendering)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "sources": list(set(sources)),
                "tool": tool_used
            })

elif page == "AI Copilot (Full Screen)":
    st.title("Manager Copilot")
    tabs = st.tabs(["Chat", "Sources"])

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
        st.session_state.copilot_messages.append({
            "role": "assistant",
            "content": "Welcome to the full-screen Copilot. Ask for metrics or insights. For example: 'List 5 agent names' or 'Why are customers calling about blue screens?'"
        })

    with tabs[0]:
        for message in st.session_state.copilot_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message and message["sources"]:
                    st.caption(f"Sources attached: {len(message['sources'])}")
                if debug_tool and message.get("tool"):
                    st.caption(f"Tool: {message['tool'].upper()}")

        if prompt := st.chat_input("Type your question for the Auditor Copilot..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.copilot_messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Analyzing with the Hybrid Orchestrator..."):
                    result = ask_hybrid(prompt)
                    response = result.get("answer", "")
                    sources = result.get("sources", [])
                    tool_used = result.get("tool", "")
                    st.markdown(response)
                    if debug_tool and tool_used:
                        st.caption(f"Tool: {tool_used.upper()}")
            st.session_state.copilot_messages.append({
                "role": "assistant",
                "content": response,
                "sources": list(set(sources)),
                "tool": tool_used
            })

    with tabs[1]:
        st.subheader("Citations (Call IDs)")
        if any(m.get("sources") for m in st.session_state.copilot_messages if m["role"] == "assistant"):
            shown = set()
            for msg in reversed(st.session_state.copilot_messages):
                if msg.get("sources"):
                    for cid in msg["sources"]:
                        if cid not in shown:
                            st.write(f"- Call ID: {cid}")
                            shown.add(cid)
        else:
            st.info("No sources to display yet. Ask a question that requires transcript context.")

# --- Placeholder for other pages ---
elif page == "Agent Dashboard":
    st.title("Agent Dashboard")
    st.write("Agent-specific performance metrics and feedback will appear here.")

elif page == "Admin Settings (QSDD)":
    st.title("Admin Settings (QSDD)")
    import duckdb
    import pandas as pd
    import sys, os
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    TOOLS_DIR = os.path.join(BASE_DIR, "tools")
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)
    import qsdd_admin
    cols, rows = qsdd_admin.fetch_rules()
    st.subheader("Current Rules")
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No rules found.")
    st.divider()
    st.subheader("Add Rule")
    with st.form("add_rule_form"):
        sec = st.text_input("Section Name")
        crit = st.text_input("Criteria Name")
        sec_w = st.number_input("Section Weight", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
        crit_w = st.number_input("Criteria Weight", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
        eff_w = st.number_input("Effective Weight", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
        en = st.checkbox("Enabled", value=True)
        wtc = st.text_area("What To Check")
        wnc = st.text_area("When To Check")
        good = st.text_area("Good Example")
        bad = st.text_area("Bad Example")
        score_m = st.text_input("Scoring Method")
        submitted = st.form_submit_button("Add")
        if submitted and sec and crit:
            fid = qsdd_admin.add_rule(sec, crit, sec_w, crit_w, eff_w, en, wtc, wnc, good, bad, score_m)
            st.success(f"Added rule with ID {fid}")
            st.experimental_rerun()
    st.divider()
    st.subheader("Update Rule")
    cols2, rows2 = qsdd_admin.fetch_rules()
    options = []
    for r in rows2:
        idx = cols2.index("framework_id")
        name_idx = cols2.index("criteria_name")
        options.append((r[idx], r[name_idx]))
    if options:
        sel = st.selectbox("Select Rule", options, format_func=lambda x: f"{x[0]} - {x[1]}")
        if sel:
            fid_sel = sel[0]
            with st.form("update_rule_form"):
                up_sec = st.text_input("Section Name (leave blank to keep)")
                up_crit = st.text_input("Criteria Name (leave blank to keep)")
                up_sec_w = st.text_input("Section Weight (blank keep)")
                up_crit_w = st.text_input("Criteria Weight (blank keep)")
                up_eff_w = st.text_input("Effective Weight (blank keep)")
                up_en = st.selectbox("Enabled", ["keep", "true", "false"])
                up_wtc = st.text_area("What To Check (blank keep)")
                up_wnc = st.text_area("When To Check (blank keep)")
                up_good = st.text_area("Good Example (blank keep)")
                up_bad = st.text_area("Bad Example (blank keep)")
                up_score_m = st.text_input("Scoring Method (blank keep)")
                sub_up = st.form_submit_button("Update")
                if sub_up:
                    payload = {}
                    if up_sec: payload["section_name"] = up_sec
                    if up_crit: payload["criteria_name"] = up_crit
                    if up_sec_w: payload["section_weight"] = float(up_sec_w)
                    if up_crit_w: payload["criteria_weight"] = float(up_crit_w)
                    if up_eff_w: payload["effective_weight"] = float(up_eff_w)
                    if up_en != "keep": payload["enabled"] = (up_en == "true")
                    if up_wtc: payload["what_to_check"] = up_wtc
                    if up_wnc: payload["when_to_check"] = up_wnc
                    if up_good: payload["good_example"] = up_good
                    if up_bad: payload["bad_example"] = up_bad
                    if up_score_m: payload["scoring_method"] = up_score_m
                    qsdd_admin.update_rule(fid_sel, **payload)
                    st.success("Rule updated")
                    st.experimental_rerun()
    st.divider()
    st.subheader("Delete Rule")
    cols3, rows3 = qsdd_admin.fetch_rules()
    options2 = []
    for r in rows3:
        idx = cols3.index("framework_id")
        name_idx = cols3.index("criteria_name")
        options2.append((r[idx], r[name_idx]))
    if options2:
        sel2 = st.selectbox("Select Rule to Delete", options2, format_func=lambda x: f"{x[0]} - {x[1]}", key="del_sel")
        if sel2:
            if st.button("Delete Selected Rule"):
                qsdd_admin.delete_rule(sel2[0])
                st.success("Rule deleted")
                st.experimental_rerun()
