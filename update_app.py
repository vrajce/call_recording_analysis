import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block 1: session_state.messages history
orig1 = '''        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])'''
repl1 = '''        # Display chat history
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
                st.markdown(message["content"])'''

# Replace block 2: live response for message
orig2 = '''                    result = ask_hybrid(prompt)
                    response = result.get("answer", "")
                    sources = result.get("sources", [])
                    tool_used = result.get("tool", "")

                    st.markdown(response)'''
repl2 = '''                    result = ask_hybrid(prompt)
                    response = result.get("answer", "")
                    sources = result.get("sources", [])
                    tool_used = result.get("tool", "")
                    state = result.get("state", {})

                    if state:
                        with st.expander(" Show thinking", expanded=False):
                            st.markdown(f"**Routing Engine:** Decided to use {state.get('route', 'unknown')}")
                            if state.get("route") == "sql":
                                st.markdown("**SQL Query Executed:**")
                                st.code(state.get("sql_query", ""), language="sql")
                            if state.get("sql_error"):
                                st.markdown("**Error Handled:**")
                                st.error(state.get("sql_error"))

                    st.markdown(response)'''

# append state
orig3 = '''            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": list(set(sources)),
                "tool": tool_used
            })'''
repl3 = '''            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": list(set(sources)),
                "tool": tool_used,
                "state": state
            })'''

# Replace block 4: session_state.copilot_messages history
orig4 = '''    with tabs[0]:
        for message in st.session_state.copilot_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])'''
repl4 = '''    with tabs[0]:
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
                st.markdown(message["content"])'''

# Replace block 5: copilot live response
orig5 = '''                    result = ask_hybrid(prompt)
                    response = result.get("answer", "")
                    sources = result.get("sources", [])
                    tool_used = result.get("tool", "")
                    st.markdown(response)'''
repl5 = '''                    result = ask_hybrid(prompt)
                    response = result.get("answer", "")
                    sources = result.get("sources", [])
                    tool_used = result.get("tool", "")
                    state = result.get("state", {})

                    if state:
                        with st.expander(" Show thinking", expanded=False):
                            st.markdown(f"**Routing Engine:** Decided to use {state.get('route', 'unknown')}")
                            if state.get("route") == "sql":
                                st.markdown("**SQL Query Executed:**")
                                st.code(state.get("sql_query", ""), language="sql")
                            if state.get("sql_error"):
                                st.markdown("**Error Handled:**")
                                st.error(state.get("sql_error"))
                    st.markdown(response)'''

# append state to copilot
orig6 = '''            st.session_state.copilot_messages.append({
                "role": "assistant",
                "content": response,
                "sources": list(set(sources)),
                "tool": tool_used
            })'''
repl6 = '''            st.session_state.copilot_messages.append({
                "role": "assistant",
                "content": response,
                "sources": list(set(sources)),
                "tool": tool_used,
                "state": state
            })'''

content = content.replace(orig1, repl1)
content = content.replace(orig2, repl2)
content = content.replace(orig3, repl3)
content = content.replace(orig4, repl4)
content = content.replace(orig5, repl5)
content = content.replace(orig6, repl6)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
