# Epic: Refactor LangChain to LangGraph Hybrid Agent
**Context:** I am building "KenexAI", an AI Copilot for customer support managers. I have an existing Streamlit frontend and a Python backend (`chat_backend.py`). Currently, I am using a linear LangChain pipeline, but my AI keeps trying to use RAG to answer math/metric questions. 

**The Goal:** I need to refactor my orchestration logic to use **LangGraph**. I want a state machine that intelligently routes queries to either a self-healing SQL pipeline or a RAG pipeline.

**My Tech Stack (DO NOT CHANGE THESE):**
- LLM: `ChatNebius` (meta-llama/Llama-3.3-70B-Instruct)
- Database: Local DuckDB (`call_quality.duckdb`)
- Vector Store: ChromaDB with `ParentDocumentRetriever` (already implemented)
- UI: Streamlit

## Architecture Requirements (The LangGraph)
Please implement the following LangGraph workflow in my `chat_backend.py`. 

### 1. Define the Graph State (`TypedDict`)
Create a `State` class with these keys:
- `question` (str)
- `schema` (str): The DuckDB tables/columns.
- `route` (str): 'sql' or 'rag'.
- `sql_query` (str): The generated DuckDB query.
- `sql_results` (str): The output from DuckDB.
- `sql_error` (str): DuckDB execution error messages.
- `retries` (int): Counter for SQL self-correction.
- `rag_context` (str): Retrieved transcript text.
- `final_answer` (str): The manager-ready response.

### 2. Implement the Nodes
Write clean Python functions for these nodes:
- **`router_node`**: LLM analyzes `question`. If it asks for metrics, counts, rankings, averages, or agent names, return 'sql'. If it asks about tone, reasons, or transcript details, return 'rag'.
- **`generate_sql_node`**: LLM reads `question` and `schema` to write DuckDB SQL. *Crucial:* If `sql_error` is present in the state, the prompt must instruct the LLM to fix its previous query based on the error.
- **`execute_sql_node`**: Runs the SQL against DuckDB. If successful, clear `sql_error` and populate `sql_results`. If it fails, catch the exception, populate `sql_error`, and increment `retries`.
- **`retrieve_rag_node`**: Uses my existing `retriever.invoke()` to fetch documents into `rag_context`.
- **`synthesize_node`**: LLM takes `sql_results` (if SQL route) or `rag_context` (if RAG route) and writes the `final_answer`.

### 3. Implement the Edges (Routing Logic)
- **Conditional Edge 1 (Post-Router):** Go to `generate_sql_node` OR `retrieve_rag_node` based on `route`.
- **Conditional Edge 2 (Self-Healing SQL):** After `execute_sql_node`:
  - If `sql_error` is NOT empty AND `retries` < 3 -> Loop back to `generate_sql_node`.
  - If `sql_error` is empty OR `retries` >= 3 -> Go to `synthesize_node`.

### 4. Graph Compilation
Compile this into a `StateGraph`, set the entry point to `router_node`, and create a main execution function `ask_hybrid(query)` that takes a string, runs it through the compiled graph, and returns a dictionary with the `final_answer`.

**Constraints:**
- Do not use `SQLDatabaseChain` or `create_sql_agent`. Build the nodes manually using LangChain expression language (LCEL) or standard LLM invokes.
- Keep the code modular and heavily commented so I can present it clearly to hackathon judges.