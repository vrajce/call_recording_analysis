with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('                thought_container = st.status('):
        new_lines.append('                    thought_container = st.status(" Analyzing with Orchestrator...", expanded=True)\n')
        continue
    if line.startswith('                final_result = {}'):
        new_lines.append('                    final_result = {}\n')
        continue
    if line.startswith('                state = {}'):
        new_lines.append('                    state = {}\n')
        continue
    if line.startswith('                for update in ask_hybrid_stream(prompt):'):
        new_lines.append('                    for update in ask_hybrid_stream(prompt):\n')
        continue
    if line.startswith('                    if update["type"] == "step":'):
        new_lines.append('                        if update["type"] == "step":\n')
        continue
    if line.startswith('                        node = update["node"]'):
        new_lines.append('                            node = update["node"]\n')
        continue
    if line.startswith('                        node_state = update["state"]'):
        new_lines.append('                            node_state = update["state"]\n')
        continue
    if line.startswith('                        state.update(node_state)'):
        new_lines.append('                            state.update(node_state)\n')
        continue
    if line.startswith('                        if node == "router_node":'):
        new_lines.append('                            if node == "router_node":\n')
        continue
    if line.startswith('                            thought_container.write(f"** Route Selected:** {node_state.get('):
        new_lines.append('                                thought_container.write(f"** Route Selected:** {node_state.get(\'route\')}")\n')
        continue
    if line.startswith('                        elif node == "generate_sql_node":'):
        new_lines.append('                            elif node == "generate_sql_node":\n')
        continue
    if line.startswith('                            thought_container.write(f"** Generated SQL:**")'):
        new_lines.append('                                thought_container.write(f"** Generated SQL:**")\n')
        continue
    if line.startswith('                            thought_container.code(node_state.get("sql_query")'):
        new_lines.append('                                thought_container.code(node_state.get("sql_query"), language="sql")\n')
        continue
    if line.startswith('                        elif node == "execute_sql_node":'):
        new_lines.append('                            elif node == "execute_sql_node":\n')
        continue
    if line.startswith('                            if node_state.get("sql_error"):'):
        new_lines.append('                                if node_state.get("sql_error"):\n')
        continue
    if line.startswith('                                thought_container.error(f"** SQL Error:**'):
        new_lines.append('                                    thought_container.error(f"** SQL Error:** {node_state.get(\'sql_error\')}")\n')
        continue
    if line.startswith('                            else:'):
        new_lines.append('                                else:\n')
        continue
    if line.startswith('                                thought_container.success(f"** SQL Exectued Successfully**")'):
        new_lines.append('                                    thought_container.success(f"** SQL Exectued Successfully**")\n')
        continue
    if line.startswith('                        elif node == "retrieve_rag_node":'):
        new_lines.append('                            elif node == "retrieve_rag_node":\n')
        continue
    if line.startswith('                            thought_container.write(f"** Retrieved Context from Vector Store**")'):
        new_lines.append('                                thought_container.write(f"** Retrieved Context from Vector Store**")\n')
        continue
    if line.startswith('                        elif node == "synthesize_node":'):
        new_lines.append('                            elif node == "synthesize_node":\n')
        continue
    if line.startswith('                            thought_container.write(f"** Synthesizing final response...**")'):
        new_lines.append('                                thought_container.write(f"** Synthesizing final response...**")\n')
        continue
    if line.startswith('                    elif update["type"] == "final":'):
        new_lines.append('                        elif update["type"] == "final":\n')
        continue
    if line.startswith('                        final_result = update'):
        new_lines.append('                            final_result = update\n')
        continue
    if line.startswith('                        state = update.get("state", state)'):
        new_lines.append('                            state = update.get("state", state)\n')
        continue
    if line.startswith('                        thought_container.update(label=" Analysis Complete"'):
        new_lines.append('                            thought_container.update(label=" Analysis Complete", state="complete", expanded=False)\n')
        continue
    if line.startswith('                    elif update["type"] == "error":'):
        new_lines.append('                        elif update["type"] == "error":\n')
        continue
    if line.startswith('                        thought_container.error(f" Error:'):
        new_lines.append('                            thought_container.error(f" Error: {update[\'error\']}")\n')
        continue
    if line.startswith('                        thought_container.update(label=" Analysis Failed"'):
        new_lines.append('                            thought_container.update(label=" Analysis Failed", state="error", expanded=False)\n')
        continue
    if line.startswith('                response = final_result.get("answer", "") if final_result else ""'):
        new_lines.append('                    response = final_result.get("answer", "") if final_result else ""\n')
        continue
    if line.startswith('                sources = final_result.get("sources", []) if final_result else []'):
        new_lines.append('                    sources = final_result.get("sources", []) if final_result else []\n')
        continue
    if line.startswith('                tool_used = final_result.get("tool", "") if final_result else ""'):
        new_lines.append('                    tool_used = final_result.get("tool", "") if final_result else ""\n')
        continue
    if line.startswith('                st.write_stream((char for char in response))'):
        new_lines.append('                    st.write_stream((char for char in response))\n')
        continue
    if line.startswith('                if debug_tool and tool_used:'):
        new_lines.append('                    if debug_tool and tool_used:\n')
        continue
    if line.startswith('                    st.caption(f"Tool:'):
        new_lines.append('                        st.caption(f"Tool: {tool_used.upper()}")\n')
        continue
    if line.startswith('            st.session_state.copilot_messages.append({'):
        new_lines.append('                st.session_state.copilot_messages.append({\n')
        continue
    new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
