import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add ask_hybrid_stream to imports
content = content.replace("from chat_backend import ask_hybrid", "from chat_backend import ask_hybrid, ask_hybrid_stream")

# Replace first execution block (Manager Dashboard)
orig1 = '''            with st.chat_message("assistant"):
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
                        with st.expander(" See Sources (Call IDs)"):
                            for source_id in set(sources):
                                st.write(f"- Call ID: {source_id}")

            # Append assistant message to history'''
repl1 = '''            with st.chat_message("assistant"):
                thought_container = st.status(" Analyzing with Orchestrator...", expanded=True)
                final_result = {}
                
                for update in ask_hybrid_stream(prompt):
                    if update["type"] == "step":
                        node = update["node"]
                        state = update["state"]
                        if node == "router_node":
                            thought_container.write(f"** Route Selected:** {state.get('route')}")
                        elif node == "generate_sql_node":
                            thought_container.write(f"** Generated SQL:**")
                            thought_container.code(state.get("sql_query"), language="sql")
                        elif node == "execute_sql_node":
                            if state.get("sql_error"):
                                thought_container.error(f"** SQL Error:** {state.get('sql_error')}")
                            else:
                                thought_container.success(f"** SQL Exectued Successfully**")
                        elif node == "retrieve_rag_node":
                            thought_container.write(f"** Retrieved Context from Vector Store**")
                        elif node == "synthesize_node":
                            thought_container.write(f"** Synthesizing final response...**")
                    elif update["type"] == "final":
                        final_result = update
                        thought_container.update(label=" Analysis Complete", state="complete", expanded=False)
                    elif update["type"] == "error":
                        thought_container.error(f" Error: {update['error']}")
                        thought_container.update(label=" Analysis Failed", state="error", expanded=False)

                response = final_result.get("answer", "") if final_result else ""
                sources = final_result.get("sources", []) if final_result else []
                tool_used = final_result.get("tool", "") if final_result else ""
                
                st.write_stream((char for char in response))  # Token stream effect

                if debug_tool and tool_used:
                    st.caption(f"Tool: {tool_used.upper()}")

                # Add sources in an expander for verification
                if sources:
                    with st.expander(" See Sources (Call IDs)"):
                        for source_id in set(sources):
                            st.write(f"- Call ID: {source_id}")

            # Append assistant message to history'''

# Same logic for Copilot dashboard
orig2 = '''            with st.chat_message("assistant"):
                with st.spinner("Analyzing with the Hybrid Orchestrator..."):
                    result = ask_hybrid(prompt)
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
                    st.markdown(response)
                    if debug_tool and tool_used:
                        st.caption(f"Tool: {tool_used.upper()}")'''
repl2 = '''            with st.chat_message("assistant"):
                thought_container = st.status(" Analyzing with Orchestrator...", expanded=True)
                final_result = {}
                state = {}
                
                for update in ask_hybrid_stream(prompt):
                    if update["type"] == "step":
                        node = update["node"]
                        node_state = update["state"]
                        state.update(node_state)
                        if node == "router_node":
                            thought_container.write(f"** Route Selected:** {node_state.get('route')}")
                        elif node == "generate_sql_node":
                            thought_container.write(f"** Generated SQL:**")
                            thought_container.code(node_state.get("sql_query"), language="sql")
                        elif node == "execute_sql_node":
                            if node_state.get("sql_error"):
                                thought_container.error(f"** SQL Error:** {node_state.get('sql_error')}")
                            else:
                                thought_container.success(f"** SQL Exectued Successfully**")
                        elif node == "retrieve_rag_node":
                            thought_container.write(f"** Retrieved Context from Vector Store**")
                        elif node == "synthesize_node":
                            thought_container.write(f"** Synthesizing final response...**")
                    elif update["type"] == "final":
                        final_result = update
                        state = update.get("state", state)
                        thought_container.update(label=" Analysis Complete", state="complete", expanded=False)
                    elif update["type"] == "error":
                        thought_container.error(f" Error: {update['error']}")
                        thought_container.update(label=" Analysis Failed", state="error", expanded=False)

                response = final_result.get("answer", "") if final_result else ""
                sources = final_result.get("sources", []) if final_result else []
                tool_used = final_result.get("tool", "") if final_result else ""
                
                st.write_stream((char for char in response))

                if debug_tool and tool_used:
                    st.caption(f"Tool: {tool_used.upper()}")'''

content = content.replace(orig1, repl1)
content = content.replace(orig2, repl2)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Streaming replaced successfully in app.py")
