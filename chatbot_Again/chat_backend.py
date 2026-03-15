import os
from typing import Dict, List, Tuple, Optional
import duckdb


def connect(db_path: Optional[str] = None) -> duckdb.DuckDBPyConnection:
    p = db_path or os.path.join(os.getcwd(), "call_quality.duckdb")
    return duckdb.connect(p)


def list_tables(con: duckdb.DuckDBPyConnection) -> List[str]:
    rows = con.execute(
        "select table_schema, table_name from information_schema.tables "
        "where table_schema not in ('information_schema', 'pg_catalog') "
        "order by 1, 2"
    ).fetchall()
    tables = []
    for schema, name in rows:
        if schema and name:
            if schema != "main":
                tables.append(f"{schema}.{name}")
            else:
                tables.append(name)
    return tables


def get_table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> List[str]:
    q = f"pragma table_info('{table_name}')"
    rows = con.execute(q).fetchall()
    cols = []
    for r in rows:
        cols.append(r[1])
    return cols


def get_schema_catalog(con: duckdb.DuckDBPyConnection) -> str:
    parts = []
    for t in list_tables(con):
        cols = get_table_columns(con, t)
        parts.append(f"Table: {t}, Columns: {', '.join(cols)}")
    return "\n".join(parts)


def build_schema_map(con: duckdb.DuckDBPyConnection) -> Dict[str, List[str]]:
    m: Dict[str, List[str]] = {}
    for t in list_tables(con):
        m[t] = get_table_columns(con, t)
    return m


def execute_sql(con: duckdb.DuckDBPyConnection, sql: str) -> Tuple[List[str], List[Tuple]]:
    res = con.execute(sql)
    cols = [d[0] for d in res.description] if res.description else []
    rows = res.fetchall()
    return cols, rows


def _heuristic_generate_sql(query: str, schema: Dict[str, List[str]]) -> Optional[str]:
    q = query.lower()
    if "tables" in q or ("list" in q and "table" in q):
        return "select table_name from information_schema.tables where table_schema not in ('information_schema','pg_catalog') order by 1 limit 50"
    if "columns" in q and "of" in q:
        for t, cols in schema.items():
            if t.lower() in q:
                return f"select name, type from pragma_table_info('{t}')"
    if "count" in q:
        for t in schema.keys():
            return f"select count(*) as count from {t}"
    if "list" in q or "show" in q or "names" in q:
        for t, cols in schema.items():
            name_cols = [c for c in cols if c.lower() in ("name", "title")]
            if name_cols:
                return f"select {name_cols[0]} from {t} limit 10"
    return None


def _provider_generate_sql(query: str, schema_catalog: str) -> str:
    provider = os.getenv("T2SQL_PROVIDER", "").lower()
    if provider in ("", "mock"):
        raise RuntimeError("provider disabled")
    if provider == "openai":
        raise NotImplementedError("openai provider not configured")
    if provider == "nebius":
        raise NotImplementedError("nebius provider not configured")
    raise NotImplementedError("unknown provider")


def ask_text_to_sql(query: str, db_path: Optional[str] = None) -> Dict:
    con = connect(db_path)
    schema_map = build_schema_map(con)
    schema_catalog = "\n".join([f"Table: {t}, Columns: {', '.join(cols)}" for t, cols in schema_map.items()])
    sql: Optional[str] = None
    try:
        sql = _provider_generate_sql(query, schema_catalog)
    except Exception:
        sql = _heuristic_generate_sql(query, schema_map)
    if not sql:
        return {"answer": "unable to translate query", "sql": None, "rows": [], "columns": [], "tool": "sql"}
    cols, rows = execute_sql(con, sql)
    return {"answer": "ok", "sql": sql, "rows": rows, "columns": cols, "tool": "sql"}


def preview_result(columns: List[str], rows: List[Tuple], limit: int = 10) -> str:
    head = rows[:limit]
    widths = [len(c) for c in columns]
    for r in head:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], len(str(v)))
    line = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(columns))
    sep = "-+-".join("-" * widths[i] for i in range(len(columns)))
    out = [line, sep]
    for r in head:
        out.append(" | ".join(str(v).ljust(widths[i]) for i, v in enumerate(r)))
    return "\n".join(out)

