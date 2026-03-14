# KenexAI: Complete System Rebuild (V2)
**Goal:** Implement a high-fidelity, generalized AI Orchestrator that uses dynamic SQL generation and Parent-Document RAG. 

---

## Phase 1: Clean Slate Environment
- [ ] **Task 1.1:** Setup `ChatNebius` with `meta-llama/Llama-3.3-70B-Instruct` (Temperature 0).
- [ ] **Task 1.2:** Initialize `NebiusEmbeddings` (model: `BAAI/bge-en-icl`).
- [ ] **Task 1.3:** Connect to `ParentDocumentRetriever` using the existing `./advanced_vector_store` and `./parent_records`.
- [ ] **Task 1.4:** **DELETE** all existing `ask_hybrid`, `ask_bot`, and manual `if/else` keyword logic in `chat_backend.py`.

## Phase 2: The "Map" (Schema Discovery)
- [ ] **Task 2.1:** Create a function `get_schema_catalog()`. 
- [ ] **Task 2.2:** It must query DuckDB's `information_schema.columns` or use `PRAGMA table_info` to return a string: "Table: [name], Columns: [col1, col2...]". 
- [ ] **Importance:** This is the ONLY way the LLM knows how to write SQL.

## Phase 3: The 3-Step Orchestration Pipeline
Implement the new `ask_hybrid(query)` function using this flow:

### Step A: The Planner (The Brain)
- [ ] **Instruction:** The LLM receives the `query` + `schema_catalog`.
- [ ] **Output:** It must return a JSON object: 
  `{"mode": "sql"|"rag"|"hybrid", "sql": "...", "rag": "...", "reasoning": "..."}`
- [ ] **Rule:** If the user wants counts, rankings, or lists, the mode MUST be `sql`.

### Step B: The Executor (The Hands)
- [ ] **SQL Branch:** Execute the generated `sql` query directly against DuckDB. Return the dataframe as a string.
- [ ] **RAG Branch:** Execute `retriever.invoke(rag_query)`. Collect the `page_content` and `call_id` from metadata.

### Step C: The Synthesizer (The Voice)
- [ ] **Instruction:** Pass the original query + SQL results + RAG context + QSDD rules back to the LLM.
- [ ] **Goal:** Write a professional audit response. If SQL data is provided, use those exact numbers. If RAG data is provided, use it to explain "why."

## Phase 4: UI & Metadata Return
- [ ] **Task 4.1:** The `ask_hybrid` function must return a dictionary: 
  `{"answer": "...", "sources": [...], "tool": "sql"|"rag"|"hybrid"}`
- [ ] **Task 4.2:** Ensure `app.py` is updated to display the `tool` used in a small badge for transparency.

## Phase 5: Testing the "New World"
- [ ] **Test 1:** "List 10 agent names." -> Verify it uses SQL.
- [ ] **Test 2:** "What is the average score for the Hardware category?" -> Verify it uses SQL.
- [ ] **Test 3:** "Why did Call ID 123 fail the Security rule?" -> Verify it uses RAG.