import os
import sys
import duckdb
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from chat_backend import get_qsdd_context


def main():
    print("--- QSDD Context ---")
    print(get_qsdd_context())
    con = duckdb.connect("call_quality.duckdb")
    print("--- Counts ---")
    print("total rows:", con.execute("SELECT COUNT(*) FROM qsdd_framework").fetchone()[0])
    print("enabled rows:", con.execute("SELECT COUNT(*) FROM qsdd_framework WHERE enabled=TRUE").fetchone()[0])
    print("--- Sample ---")
    rows = con.execute(
        "SELECT section_name, criteria_name, effective_weight, what_to_check FROM qsdd_framework WHERE enabled=TRUE ORDER BY section_name, effective_weight DESC, criteria_name LIMIT 5"
    ).fetchall()
    for r in rows:
        print(r)
    con.close()


if __name__ == "__main__":
    main()
