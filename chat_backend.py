import os
from dotenv import load_dotenv
from langchain_nebius import ChatNebius, NebiusEmbeddings
from langchain_community.vectorstores import Chroma
try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
except Exception:
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
# SQL disabled for RAG-only mode
# from langchain_community.utilities import SQLDatabase
# from sqlalchemy import create_engine
import re
import math
import json

# Load environment variables
load_dotenv()
if not os.getenv("NEBIUS_API_KEY"):
    raise RuntimeError("NEBIUS_API_KEY not found in environment. Set it in a local .env.")

embeddings = NebiusEmbeddings(model="BAAI/bge-en-icl")

def get_qsdd_rules_prompt() -> str:
    try:
        import duckdb
        con = duckdb.connect("call_quality.duckdb")
        tables = [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()]
        if not tables:
            tables = [r[0] for r in con.execute("PRAGMA show_tables").fetchall()]
        qsdd_table = None
        for t in tables:
            if "qsdd" in (t or "").lower():
                qsdd_table = t
                break
        if not qsdd_table:
            con.close()
            return "No QSDD rules found."
        cols = [r[1] for r in con.execute(f"PRAGMA table_info('{qsdd_table}')").fetchall()]
        colset = {c.lower() for c in cols}
        has_enabled = "enabled" in colset
        if {"section_name", "criteria_name"}.issubset(colset) and (("effective_weight" in colset) or ("weight" in colset)):
            weight_col = "effective_weight" if "effective_weight" in colset else "weight"
            check_col = "what_to_check" if "what_to_check" in colset else ("description" if "description" in colset else None)
            where_clause = "WHERE enabled = TRUE" if has_enabled else ""
            order_clause = f"ORDER BY section_name, {weight_col} DESC, criteria_name"
            select_cols = f"section_name, criteria_name, {weight_col}" + (f", {check_col}" if check_col else "")
            rows = con.execute(f"SELECT {select_cols} FROM {qsdd_table} {where_clause} {order_clause}").fetchall()
            con.close()
            if not rows:
                return "No QSDD rules found."
            by_section = {}
            for row in rows:
                sec = row[0]
                crit = row[1]
                wt = row[2]
                check = row[3] if len(row) > 3 else ""
                by_section.setdefault(sec or "General", []).append((crit, wt, check))
            lines = []
            for sec, items in by_section.items():
                lines.append(f"- {sec}:")
                for crit, wt, check in items:
                    pct = round(wt * 100, 2) if wt and wt <= 1 else round(wt or 0, 2)
                    lines.append(f"  • {crit} ({pct}%): {check}")
            return "\n".join(lines)
        elif {"criteria_name", "weight"}.issubset(colset):
            where_clause = "WHERE enabled = TRUE" if has_enabled else ""
            rows = con.execute(f"SELECT criteria_name, weight, COALESCE(description, '') FROM {qsdd_table} {where_clause} ORDER BY weight DESC, criteria_name").fetchall()
            con.close()
            if not rows:
                return "No QSDD rules found."
            lines = []
            for name, wt, desc in rows:
                pct = round(wt * 100, 2) if wt and wt <= 1 else round(wt or 0, 2)
                lines.append(f"- {name} ({pct}%): {desc}")
            return "\n".join(lines)
        else:
            sample = con.execute(f"SELECT * FROM {qsdd_table} LIMIT 5").df()
            con.close()
            return sample.to_string(index=False)
    except Exception:
        return "No QSDD rules found."

def get_advanced_retriever():
    try:
        from langchain.retrievers import ParentDocumentRetriever
        from langchain.storage import LocalFileStore, create_kv_docstore
    except Exception:
        from langchain_classic.retrievers import ParentDocumentRetriever
        from langchain_classic.storage import LocalFileStore, create_kv_docstore
    vectorstore = Chroma(
        collection_name="advanced_transcripts",
        embedding_function=embeddings,
        persist_directory="./advanced_vector_store",
    )
    fs = LocalFileStore("./parent_records")
    store = create_kv_docstore(fs)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    return ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
        search_kwargs={"k": 7},
    )

def get_basic_retriever():
    vector_store = Chroma(
        persist_directory="./vector_store",
        embedding_function=embeddings,
    )
    return vector_store.as_retriever(search_kwargs={"k": 7})

try:
    retriever = get_advanced_retriever()
except Exception:
    retriever = get_basic_retriever()

# Initialize the LLM (hosted on Nebius)
llm = ChatNebius(
    model="meta-llama/Llama-3.3-70B-Instruct", 
    temperature=0
)

# Create a System Prompt
dynamic_qsdd = get_qsdd_rules_prompt()
system_prompt = (
    "You are the  Senior Auditor. Operate purely on transcript evidence using the QSDD framework.\n\n"
    "### OPERATIONAL GUIDELINES:\n"
    "1. TRANSCRIPT ANALYSIS: Identify agent behaviors, customer emotions, and technical steps strictly from transcript context.\n"
    "2. QSDD COMPLIANCE: Evaluate against pillars:\n"
    "   - Security & Authentication\n"
    "   - Technical Accuracy\n"
    "   - Professionalism & Tone\n"
    "3. EVIDENCE-BASED: Do not invent facts or numbers. Always cite [Call ID]. Use direct quotes when relevant.\n"
    "4. STRUCTURE: Use clear sections and concise bullet points.\n"
    "5. UNCERTAINTY: If you don't know the answer, say 'I don't know' and avoid speculation.\n\n"
    "### QSDD RULES (Dynamic):\n"
    f"{dynamic_qsdd}\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Combine LLM and prompt into a document chain
question_answer_chain = create_stuff_documents_chain(llm, prompt)

# Combine with the retriever to create the final retrieval_chain
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

def ask_bot(query: str) -> dict:
    try:
        response = rag_chain.invoke({"input": query})
        return {
            "answer": response.get("answer", ""),
            "sources": [doc.metadata.get("call_id") for doc in response.get("context", []) if hasattr(doc, "metadata")]
        }
    except Exception as e:
        return {
            "answer": f"Unable to complete the request: {e}",
            "sources": []
        }

def ask_manager(query: str) -> dict:
    try:
        q = query.lower()
        if any(k in q for k in ["count", "how many", "total calls"]):
            import duckdb
            con = duckdb.connect("call_quality.duckdb")
            total = con.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0]
            con.close()
            return {"answer": f"Total calls: {total}", "sources": []}
        return ask_bot(query)
    except Exception as e:
        return {"answer": f"Unable to process the request: {e}", "sources": []}

def get_qsdd_context() -> str:
    try:
        import duckdb
        con = duckdb.connect("call_quality.duckdb")
        tables = [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()]
        if not tables:
            tables = [r[0] for r in con.execute("PRAGMA show_tables").fetchall()]
        qsdd_table = None
        for t in tables:
            if "qsdd" in (t or "").lower():
                qsdd_table = t
                break
        if not qsdd_table:
            con.close()
            return "No QSDD rules found."
        cols = [r[1] for r in con.execute(f"PRAGMA table_info('{qsdd_table}')").fetchall()]
        colset = {c.lower() for c in cols}
        has_enabled = "enabled" in colset
        if {"section_name", "criteria_name"}.issubset(colset) and (("effective_weight" in colset) or ("weight" in colset)):
            weight_col = "effective_weight" if "effective_weight" in colset else "weight"
            check_col = "what_to_check" if "what_to_check" in colset else ("description" if "description" in colset else None)
            where_clause = "WHERE enabled = TRUE" if has_enabled else ""
            order_clause = f"ORDER BY section_name, {weight_col} DESC, criteria_name"
            select_cols = f"section_name, criteria_name, {weight_col}" + (f", {check_col}" if check_col else "")
            rows = con.execute(f"SELECT {select_cols} FROM {qsdd_table} {where_clause} {order_clause}").fetchall()
            con.close()
            if not rows:
                return "No QSDD rules found."
            by_section = {}
            for row in rows:
                sec = row[0]
                crit = row[1]
                wt = row[2]
                check = row[3] if len(row) > 3 else ""
                by_section.setdefault(sec or "General", []).append((crit, wt, check))
            lines = []
            for sec, items in by_section.items():
                lines.append(f"- {sec}:")
                for crit, wt, check in items:
                    pct = round(wt * 100, 2) if wt and wt <= 1 else round(wt or 0, 2)
                    lines.append(f"  • {crit} ({pct}%): {check}")
            return "\n".join(lines)
        elif {"criteria_name", "weight"}.issubset(colset):
            where_clause = "WHERE enabled = TRUE" if has_enabled else ""
            rows = con.execute(f"SELECT criteria_name, weight, COALESCE(description, '') FROM {qsdd_table} {where_clause} ORDER BY weight DESC, criteria_name").fetchall()
            con.close()
            if not rows:
                return "No QSDD rules found."
            lines = []
            for name, wt, desc in rows:
                pct = round(wt * 100, 2) if wt and wt <= 1 else round(wt or 0, 2)
                lines.append(f"- {name} ({pct}%): {desc}")
            return "\n".join(lines)
        else:
            sample = con.execute(f"SELECT * FROM {qsdd_table} LIMIT 5").df()
            con.close()
            return sample.to_string(index=False)
    except Exception:
        return "No QSDD rules found."

# SQL catalog disabled in RAG-only mode
# def get_schema_catalog() -> str:
#     try:
#         import duckdb
#         con = duckdb.connect("call_quality.duckdb")
#         tables = [r[0] for r in con.execute(
#             "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
#         ).fetchall()]
#         if not tables:
#             tables = [r[0] for r in con.execute("PRAGMA show_tables").fetchall()]
#         lines = []
#         for t in tables:
#             try:
#                 cols = con.execute(f"PRAGMA table_info('{t}')").fetchall()
#                 colnames = [r[1] for r in cols]
#                 lines.append(f"{t}: {', '.join(colnames)}")
#             except Exception:
#                 continue
#         con.close()
#         return "\n".join(lines)
#     except Exception:
#         return ""

last_tool_used = None
last_sources = []

# SQL database disabled in RAG-only mode

# @tool("metrics_sql", return_direct=False)
# def metrics_sql(query: str) -> str:
#     """Calculates mathematical truths. Use for averages, totals, and identifying outliers by score."""
#     global last_tool_used, last_sources
#     last_tool_used = "sql"
#     last_sources = []
#     try:
#         return db.run(query)
#     except Exception as e:
#         return f"SQL error: {e}"

@tool("transcript_rag", return_direct=False)
def transcript_rag(question: str) -> str:
    """Audits human behavior. Use to find direct evidence of QSDD violations, customer sentiment, and specific troubleshooting steps."""
    global last_tool_used, last_sources
    last_tool_used = "rag"
    last_sources = []
    qsdd_ctx = get_qsdd_rules_prompt()
    system_text = (
        "You are the  Manager Copilot. You have access to a Vector Store "
        "containing call transcripts. Use the following QSDD Framework for audits:\n"
        "{qsdd_context}\n"
        "Always cite Call IDs from the metadata when possible."
    )
    local_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_text),
            ("human", "{input}"),
        ]
    )
    local_chain = create_stuff_documents_chain(llm, local_prompt)
    local_rag = create_retrieval_chain(retriever, local_chain)
    try:
        resp = local_rag.invoke({"input": question, "qsdd_context": qsdd_ctx})
        last_sources = []
        for doc in resp.get("context", []) if isinstance(resp, dict) else []:
            mid = getattr(doc, "metadata", {}) if hasattr(doc, "metadata") else {}
            cid = mid.get("call_id") or mid.get("contact_id")
            if cid:
                last_sources.append(cid)
        ans = resp.get("answer", "")
        return _ensure_citations(ans, last_sources)
    except Exception as e:
        return f"RAG error: {e}"

def get_last_tool_used() -> str:
    return last_tool_used or ""

tools = [transcript_rag]
hybrid_system = (
    "You are the KenexAI Senior Auditor. Operate ONLY on transcript evidence.\n"
    "OFFICIAL QSDD FRAMEWORK:\n"
    "{qsdd_context}\n\n"
    "OPERATIONAL PROTOCOLS:\n"
    "1. QUALITATIVE: Audit behavior, tone, and compliance using RAG.\n"
    "2. THE 'WHY' LINK: Explain failures with direct transcript evidence.\n"
    "3. CITATION: Always include [Call ID].\n"
    "4. SEVERITY: Label failures over 15% effective weight as 'CRITICAL BUSINESS RISK'.\n"
)
try:
    from langchain.agents import create_openai_tools_agent, AgentExecutor
    hybrid_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", hybrid_system),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    _agent = create_openai_tools_agent(llm, tools, hybrid_prompt)
    agent_executor = AgentExecutor(agent=_agent, tools=tools, verbose=False)
    _USE_AGENT = True
except Exception:
    try:
        from langchain.agents import create_react_agent, AgentExecutor  # fallback to ReAct agent
        react_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", hybrid_system + "\nFollow ReAct style: Thought/Action/Action Input/Observation until done."),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        _agent = create_react_agent(llm, tools, react_prompt)
        agent_executor = AgentExecutor(agent=_agent, tools=tools, verbose=False)
        _USE_AGENT = True
    except Exception:
        agent_executor = None
        _USE_AGENT = False

# SQL helpers disabled in RAG-only mode
# def _extract_sql(text: str) -> str: ...
# def _generate_sql(query: str) -> str: ...
# def _summarize_sql(q: str, r: str) -> str: ...

def _ensure_citations(ans: str, ids: list) -> str:
    uniq = []
    for x in ids or []:
        s = str(x)
        if s and s not in uniq:
            uniq.append(s)
    if not uniq:
        return ans
    for cid in uniq:
        if cid in ans:
            return ans
    head = uniq[:10]
    return ans + "\n\nCitations (Call IDs): " + ", ".join(head)

def _extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    text2 = text.strip()
    text2 = text2.strip("`")
    text2 = re.sub(r"^json\\s*", "", text2, flags=re.IGNORECASE)
    try:
        return json.loads(text2)
    except Exception:
        pass
    for m in re.finditer(r"\{[\s\S]*?\}", text):
        snippet = m.group(0)
        try:
            return json.loads(snippet)
        except Exception:
            try:
                return json.loads(snippet.replace("'", '"'))
            except Exception:
                continue
    return {}

def ask_hybrid(query: str) -> dict:
    global last_sources
    global last_tool_used
    last_tool_used = "rag"
    try:
        qsdd_ctx = get_qsdd_rules_prompt()
        base_prompt = ChatPromptTemplate.from_messages(
            [
                ("system",
                 "You are the KenexAI Senior Auditor. Operate ONLY on transcript evidence.\n"
                 "QSDD:\n{qsdd}\n"
                 "Always cite Call IDs when present."),
                ("human", "{q}"),
            ]
        )
        chain = base_prompt | llm
        try:
            docs = retriever.invoke(query)
        except Exception:
            docs = retriever.get_relevant_documents(query)
        top_docs = docs[:3] if isinstance(docs, list) else []
        ctx = "\n\n".join([getattr(d, "page_content", "") for d in top_docs])
        sources = []
        for d in top_docs:
            if hasattr(d, "metadata"):
                mid = getattr(d, "metadata", {})
                cid = mid.get("call_id") or mid.get("contact_id")
                if cid:
                    sources.append(cid)
        msg = chain.invoke({"qsdd": qsdd_ctx, "q": f"{query}\n\nContext:\n{ctx}"})
        answer = getattr(msg, "content", "") or str(msg)
        answer = _ensure_citations(answer, sources)
        return {"answer": answer, "sources": sources, "tool": "rag"}
    except Exception as e:
        try:
            resp = rag_chain.invoke({"input": query})
            ans = resp.get("answer", "")
            srcs = [d.metadata.get("call_id") for d in resp.get("context", []) if hasattr(d, "metadata")]
            return {"answer": ans or f"RAG error: {e}", "sources": srcs, "tool": "rag"}
        except Exception:
            return {"answer": f"Unable to complete the request: {e}", "sources": [], "tool": "rag"}

if __name__ == "__main__":
    # Simple CLI test
    test_query = "What common issues do customers report?"
    print(f"Testing with query: {test_query}")
    result = ask_bot(test_query)
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")
