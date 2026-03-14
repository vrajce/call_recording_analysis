import duckdb

def main():
    con = duckdb.connect("call_quality.duckdb")
    tables = [r[0] for r in con.execute("PRAGMA show_tables").fetchall()]
    print("table_count:", len(tables))
    print("tables:", ", ".join(tables))
    for t in tables:
        cols = con.execute(f"PRAGMA table_info('{t}')").fetchall()
        print("table:", t)
        print("columns:", ", ".join([c[1] for c in cols]))
    if "ai_summary" in tables:
        cols = con.execute("PRAGMA table_info('ai_summary')").fetchall()
        print("ai_summary_columns:", ", ".join([c[1] for c in cols]))
    else:
        print("ai_summary_columns:", "not_found")
    con.close()

if __name__ == "__main__":
    main()
