import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix for Copilot page
orig_copilot = '''    with tabs[0]:
        for message in st.session_state.copilot_messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and message.get("state"):
                    with st.expander(" Show thinking", expanded=False):
                        st.markdown(f"**Routing Engine:** Decided to use {message['state'].get('route', 'unknown')}")
                        if message["state"].get("route") == "sql":
                            st.markdown("**SQL Query Executed:**")
                            st.code(message["state"].get("sql_query", ""), language="sql")
                        if message["state"].get("sql_error"):
                            st.markdown("**Error Handled:**")
                            st.error(message["state"].get("sql_error"))
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message and message["sources"]:
                    st.caption(f"Sources attached: {len(message['sources'])}")
                if debug_tool and message.get("tool"):
                    st.caption(f"Tool: {message['tool'].upper()}")

        if prompt := st.chat_input("Type your question for the Auditor Copilot..."):'''

repl_copilot = '''    with tabs[0]:
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.copilot_messages:
                with st.chat_message(message["role"]):
                    if message["role"] == "assistant" and message.get("state"):
                        with st.expander(" Show thinking", expanded=False):
                            st.markdown(f"**Routing Engine:** Decided to use {message['state'].get('route', 'unknown')}")
                            if message["state"].get("route") == "sql":
                                st.markdown("**SQL Query Executed:**")
                                st.code(message["state"].get("sql_query", ""), language="sql")
                            if message["state"].get("sql_error"):
                                st.markdown("**Error Handled:**")
                                st.error(message["state"].get("sql_error"))
                    st.markdown(message["content"])
                    if message["role"] == "assistant" and "sources" in message and message["sources"]:
                        st.caption(f"Sources attached: {len(message['sources'])}")
                    if debug_tool and message.get("tool"):
                        st.caption(f"Tool: {message['tool'].upper()}")

        if prompt := st.chat_input("Type your question for the Auditor Copilot..."):
            with chat_container:'''

content = content.replace(orig_copilot, repl_copilot)

# Fix for Manager Dashboard page
orig_mgr = '''        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and message.get("state"):
                    with st.expander(" Show thinking", expanded=False):
                        st.markdown(f"**Routing Engine:** Decided to use {message['state'].get('route', 'unknown')}")
                        if message["state"].get("route") == "sql":
                            st.markdown("**SQL Query Executed:**")
                            st.code(message["state"].get("sql_query", ""), language="sql")
                        if message["state"].get("sql_error"):
                            st.markdown("**Error Handled:**")
                            st.error(message["state"].get("sql_error"))
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander(" See Sources (Call IDs)"):
                        for source_id in message["sources"]:
                            st.write(f"- Call ID: {source_id}")

        # Chat input
        if prompt := st.chat_input("e.g., Why are customers calling about blue screens?"):'''

repl_mgr = '''        # Display chat history
        mgr_container = st.container()
        
        with mgr_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message["role"] == "assistant" and message.get("state"):
                        with st.expander(" Show thinking", expanded=False):
                            st.markdown(f"**Routing Engine:** Decided to use {message['state'].get('route', 'unknown')}")
                            if message["state"].get("route") == "sql":
                                st.markdown("**SQL Query Executed:**")
                                st.code(message["state"].get("sql_query", ""), language="sql")
                            if message["state"].get("sql_error"):
                                st.markdown("**Error Handled:**")
                                st.error(message["state"].get("sql_error"))
                    st.markdown(message["content"])
                    if message["role"] == "assistant" and "sources" in message:
                        with st.expander(" See Sources (Call IDs)"):
                            for source_id in message["sources"]:
                                st.write(f"- Call ID: {source_id}")

        # Chat input
        if prompt := st.chat_input("e.g., Why are customers calling about blue screens?"):
            with mgr_container:'''

content = content.replace(orig_mgr, repl_mgr)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("UI containers mapped successfuly.")
