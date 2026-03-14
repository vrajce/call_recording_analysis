import duckdb
import sys

DB_PATH = "call_quality.duckdb"
SAMPLE_ROWS = 5

def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def main():
    con = duckdb.connect(DB_PATH)
    try:
        tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name").fetchall()
        if not tables:
            tables = con.execute("PRAGMA show_tables").fetchall()
            tables = [(t[0],) for t in tables]
        print("\n=== Tables ===")
        for t in tables:
            print(f"- {t[0]}")
        print("\n=== Details ===")
        for (tname,) in tables:
            print(f"\n--- {tname} ---")
            try:
                cols = con.execute(f"PRAGMA table_info({qident(tname)})").fetchall()
                if cols:
                    print("Columns:")
                    for c in cols:
                        print(f"  - {c[1]} ({c[2]})")
                cnt = con.execute(f"SELECT COUNT(*) FROM {qident(tname)}").fetchone()[0]
                print(f"Rows: {cnt}")
                try:
                    sample = con.execute(f"SELECT * FROM {qident(tname)} LIMIT {SAMPLE_ROWS}").df()
                    if not sample.empty:
                        print("Sample:")
                        print(sample.to_string(index=False))
                except Exception as e:
                    print(f"Sample error: {e}")
                try:
                    date_cols = [c[1] for c in cols if str(c[2]).lower() in ("date", "timestamp", "datetime")]
                    if date_cols:
                        for dc in date_cols[:3]:
                            rng = con.execute(f"SELECT MIN({qident(dc)}), MAX({qident(dc)}) FROM {qident(tname)}").fetchone()
                            print(f"Range {dc}: {rng[0]} .. {rng[1]}")
                except Exception:
                    pass
                try:
                    score_candidates = {"score", "quality_score", "avg_score", "total_score", "qs"}
                    numeric_cols = [c[1] for c in cols if any(k in c[2].lower() for k in ["int", "double", "float", "decimal"])]
                    core = [c for c in numeric_cols if c.lower() in score_candidates]
                    for nc in core[:3]:
                        stats = con.execute(f"SELECT MIN({qident(nc)}), AVG({qident(nc)}), MAX({qident(nc)}) FROM {qident(tname)}").fetchone()
                        print(f"Stats {nc}: min={stats[0]} avg={stats[1]} max={stats[2]}")
                except Exception:
                    pass
            except Exception as e:
                print(f"Error reading table {tname}: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        DB_PATH = sys.argv[1]
    if len(sys.argv) > 2:
        SAMPLE_ROWS = int(sys.argv[2])
    main()
