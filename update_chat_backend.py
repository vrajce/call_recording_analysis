import re

with open('chat_backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''
def ask_hybrid_stream(query: str):
    global last_sources
    global last_tool_used
    last_sources = []

    schema = get_schema_catalog()
    initial_state = {
        "question": query,
        "schema": schema,
        "route": "",
        "sql_query": "",
        "sql_results": "",
        "sql_error": "",
        "retries": 0,
        "rag_context": "",
        "final_answer": ""
    }

    try:
        final_state = initial_state.copy()
        for output in app_graph.stream(initial_state):
            for node_name, state_update in output.items():
                final_state.update(state_update)
                yield {"type": "step", "node": node_name, "state": state_update}
        
        ans = final_state.get("final_answer", "No answer generated.")
        route_used = final_state.get("route", "rag")

        if route_used == "rag":
            ans = _ensure_citations(ans, last_sources)

        yield {"type": "final", "answer": ans, "sources": last_sources, "tool": route_used, "state": final_state}
    except Exception as e:
        yield {"type": "error", "error": str(e)}

if __name__ == "__main__":'''

content = content.replace('if __name__ == "__main__":', new_func)

with open('chat_backend.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("chat_backend.py updated")
