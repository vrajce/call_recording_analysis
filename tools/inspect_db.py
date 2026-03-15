import duckdb


def main():
    con = duckdb.connect("call_quality.duckdb")
    show = con.execute("PRAGMA show_tables").fetchall()
    print("Tables:", [r[0] for r in show])
    for r in show:
        t = r[0]
        cols = con.execute(f"PRAGMA table_info('{t}')").fetchall()
        print("Table:", t)
        print("Columns:", [(c[1], c[2]) for c in cols])
        if t.lower() == "qsdd_framework":
            total = con.execute("SELECT COUNT(*) FROM qsdd_framework").fetchone()[0]
            enabled = con.execute("SELECT COUNT(*) FROM qsdd_framework WHERE enabled=TRUE").fetchone()[0]
            print("QSDD rows:", total, "enabled:", enabled)
    con.close()


if __name__ == "__main__":
    main()
