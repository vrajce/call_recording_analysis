import os
import json
import duckdb
from datetime import datetime

def get_qsdd_rules():
    con = duckdb.connect("call_quality.duckdb")
    tables = [r[0] for r in con.execute("PRAGMA show_tables").fetchall()]
    qsdd_table = None
    for t in tables:
        if "qsdd" in (t or "").lower():
            qsdd_table = t
            break
    if not qsdd_table:
        con.close()
        return ""
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
            return ""
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
            return ""
        lines = []
        for name, wt, desc in rows:
            pct = round(wt * 100, 2) if wt and wt <= 1 else round(wt or 0, 2)
            lines.append(f"- {name} ({pct}%): {desc}")
        return "\n".join(lines)
    else:
        sample = con.execute(f"SELECT * FROM {qsdd_table} LIMIT 5").df()
        con.close()
        return sample.to_string(index=False)

def load_hf_pipeline():
    try:
        from transformers import pipeline
    except Exception:
        return None
    model_name = os.getenv("HF_MODEL", "google/flan-t5-base")
    try:
        return pipeline("text2text-generation", model=model_name)
    except Exception:
        try:
            return pipeline("summarization", model="facebook/bart-large-cnn")
        except Exception:
            return None

def build_input(rules: str, text: str) -> str:
    return (
        "You are the KenexAI Quality Auditor.\n"
        "Task: Analyze the call transcript using the QSDD framework and return STRICT JSON ONLY.\n"
        "Output keys:\n"
        "  - summary: concise 3–6 sentence overview of the issue and resolution/status. Append: 'Note: Machine-generated, not human-intervened.'\n"
        "  - strengths: array of 2–5 short phrases highlighting good agent behaviors\n"
        "  - improvements: array of 2–5 short phrases with concrete actions to improve\n"
        "  - failed_criteria: array of strings naming violated QSDD criteria (use criteria_name), include at most 5\n"
        "Rules:\n"
        "  - Be evidence-based; do not invent facts.\n"
        "  - Do NOT include any text outside JSON.\n"
        "  - If uncertain, omit and keep JSON valid.\n\n"
        "QSDD:\n" + (rules or "No rules") + "\n\nTranscript:\n" + (text or "")
    )

def parse_result(s: str):
    try:
        return json.loads(s)
    except Exception:
        try:
            s2 = s.strip().strip("`").replace("json", "")
            return json.loads(s2)
        except Exception:
            return {
                "summary": s[:1000] + " Note: Machine-generated, not human-intervened.",
                "strengths": [],
                "improvements": [],
                "failed_criteria": []
            }

def ensure_table(con: duckdb.DuckDBPyConnection):
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_summary (
            contact_id BIGINT,
            agent_id BIGINT,
            summary VARCHAR,
            strengths VARCHAR,
            improvements VARCHAR,
            failed_criteria VARCHAR,
            model_name VARCHAR,
            version INTEGER,
            created_at TIMESTAMP
        )
        """
    )

def write_row(con: duckdb.DuckDBPyConnection, contact_id: int, data: dict, agent_id: int, model_name: str, version: int):
    summary = str(data.get("summary", "") or "")
    strengths_val = data.get("strengths", [])
    improvements_val = data.get("improvements", [])
    strengths = json.dumps(strengths_val) if isinstance(strengths_val, list) else str(strengths_val or "")
    improvements = json.dumps(improvements_val) if isinstance(improvements_val, list) else str(improvements_val or "")
    failed = data.get("failed_criteria", [])
    failed_str = json.dumps(failed) if isinstance(failed, list) else str(failed or "")
    ts = datetime.utcnow()
    con.execute(
        "INSERT INTO ai_summary (contact_id, agent_id, summary, strengths, improvements, failed_criteria, model_name, version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [contact_id, agent_id, summary, strengths, improvements, failed_str, model_name, version, ts],
    )

def main():
    con = duckdb.connect("call_quality.duckdb")
    ensure_table(con)
    con.execute("DELETE FROM ai_summary")
    rules = get_qsdd_rules()
    pipe = load_hf_pipeline()
    model_name = ""
    try:
        model_name = getattr(getattr(pipe, "model", None), "name_or_path", "") or os.getenv("HF_MODEL", "")
    except Exception:
        model_name = os.getenv("HF_MODEL", "")
    version = int(os.getenv("AI_SUMMARY_VERSION", "1"))
    rows = con.execute("SELECT contact_id, full_text FROM transcripts WHERE full_text IS NOT NULL").fetchall()
    for cid, text in rows:
        try:
            agent_id_row = con.execute("SELECT agent_id FROM calls WHERE contact_id = ?", [cid]).fetchone()
            agent_id = agent_id_row[0] if agent_id_row and agent_id_row[0] is not None else None
        except Exception:
            agent_id = None
        if pipe is None:
            parsed = {"summary": (text or "")[:800] + " Note: Machine-generated, not human-intervened.", "strengths": [], "improvements": [], "failed_criteria": []}
            write_row(con, cid, parsed, agent_id, "fallback", version)
            continue
        inp = build_input(rules, text or "")
        out = pipe(inp, max_new_tokens=512, do_sample=False)
        content = ""
        if isinstance(out, list) and out:
            o0 = out[0]
            content = o0.get("generated_text") or o0.get("summary_text") or str(o0)
        else:
            content = str(out)
        parsed = parse_result(content)
        write_row(con, cid, parsed, agent_id, model_name or "hf-model", version)
    con.close()
    print("done")

if __name__ == "__main__":
    main()
