import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="KenexAI Quality Analyzer", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Persona Dashboard:", 
                        ["Manager Dashboard", "Agent Dashboard", "Admin Settings (QSDD)"])

# --- 1. MANAGER DASHBOARD ---
if page == "Manager Dashboard":
    st.title("Manager Analytics & AI Copilot")
    
    # KPI Cards [cite: 1454-1456, 1619-1621]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Calls Analyzed", "1,402", "12 today")
    col2.metric("Average Quality Score", "82%", "Up 4%")
    col3.metric("Missing Transcripts", "3", "-1")
    col4.metric("Top Issue Category", "Hardware", "BitLocker")
    
    st.divider()
    
    # Split view: Call Log on the left, AI Copilot on the right
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("Recent Calls")
        # Mock Data representing your Fact Table
        mock_data = pd.DataFrame({
            "Call ID": ["626189712437", "626189712438", "626189712439"],
            "Agent": ["David Clark", "Priya Singh", "Rahul Sharma"],
            "Duration (s)": [2776, 320, 845],
            "Score": ["72%", "95%", "60%"],
            "Category": ["Hardware", "Billing", "Login"]
        })
        st.dataframe(mock_data, use_container_width=True)
        
        st.subheader("AI Call Deep-Dive")
        selected_call = st.selectbox("Select a Call ID to view AI Analysis:", mock_data["Call ID"])
        
        if selected_call == "626189712437":
            # This is where your LangChain JSON output goes [cite: 1440-1448, 1648-1655]
            st.info("**AI Summary:** Customer Lucas Scott called regarding a BitLocker blue screen error and insufficient C-Drive space. Agent David Clark attempted to transfer files to OneDrive and successfully pinned the necessary folders to Quick Access.")
            st.success("**Strengths:** Agent was patient and properly authenticated the user's name and location.")
            st.warning("**Improvements:** Agent failed to collect a callback number in case of disconnection.")

    with right_col:
        # Text-to-SQL Manager Chatbot [cite: 1449-1451, 1656-1658]
        st.subheader("AI Manager Copilot")
        st.markdown("Ask me anything about team performance.")
        
        # Streamlit Chat Interface
        messages = st.container(height=300)
        messages.chat_message("assistant").write("Hello! I'm your AI Data Analyst. What would you like to know?")
        
        if prompt := st.chat_input("e.g., Which agents have the lowest scores?"):
            messages.chat_message("user").write(prompt)
            # In your real app, this is where you call agent_executor.invoke(prompt)
            messages.chat_message("assistant").write("Fetching data from the warehouse... David Clark currently has the lowest authentication compliance score.")

# --- 2. AGENT DASHBOARD ---
elif page == "Agent Dashboard":
    st.title("Agent Portal: David Clark")
    st.markdown("Welcome back! Here is your personal performance breakdown.")
    
    col1, col2 = st.columns(2)
    col1.metric("Your Average Score", "74%", "-2%")
    col2.metric("Calls Handled Today", "8")
    
    st.subheader("Latest AI Feedback")
    # Displaying the GenAI recommendations specifically for the agent [cite: 1459-1461, 1624-1626]
    st.info("**Call 626189712437 (Hardware Issue):**")
    st.write("✅ **What you did well:** Great job stating your name and the account name during the greeting.")
    st.write("🎯 **Focus for next call:** Always confirm a callback number before you start troubleshooting.")

# --- 3. ADMIN SETTINGS (DYNAMIC QSDD) ---
elif page == "Admin Settings (QSDD)":
    st.title("System Configuration")
    st.markdown("Add or modify the quality evaluation framework without changing code. [cite: 1509-1510, 1544-1554]")
    
    st.subheader("Active Criteria & Weights")
    
    # Simulating the Dynamic Rules database [cite: 1332-1338]
    rule_1 = st.slider("Greeting: State Account and Agent Name", 0, 100, 20)
    rule_2 = st.slider("Authentication: Verify User ID and Callback Number", 0, 100, 30)
    rule_3 = st.slider("Offer Assistance: Use caller's name", 0, 100, 50)
    
    st.subheader("Add New Rule")
    new_rule_name = st.text_input("Criteria Name", placeholder="e.g., Apologize for wait time")
    new_rule_weight = st.number_input("Weight", min_value=0, max_value=100, value=10)
    
    if st.button("Save Configuration to Database"):
        st.success("Successfully updated the QSDD! The AI Evaluator will use these new rules on the next call.")