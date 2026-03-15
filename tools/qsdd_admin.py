import duckdb
import uuid
from datetime import datetime

DB_PATH = "call_quality.duckdb"

def connect():
    return duckdb.connect(DB_PATH)

def fetch_rules():
    con = connect()
    rows = con.execute("SELECT * FROM qsdd_framework ORDER BY section_name, effective_weight DESC, criteria_name").fetchall()
    cols = [d[0] for d in con.execute("SELECT * FROM qsdd_framework LIMIT 1").description] if rows else [d[0] for d in con.execute("PRAGMA table_info('qsdd_framework')").fetchall()]
    con.close()
    return cols, rows

def add_rule(section_name, criteria_name, section_weight, criteria_weight, effective_weight, enabled, what_to_check="", when_to_check="", good_example="", bad_example="", scoring_method=""):
    con = connect()
    fid = str(uuid.uuid4())
    ts = datetime.utcnow()
    con.execute(
        "INSERT INTO qsdd_framework (framework_id, section_name, criteria_name, section_weight, criteria_weight, effective_weight, enabled, what_to_check, when_to_check, good_example, bad_example, scoring_method, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [fid, section_name, criteria_name, float(section_weight or 0), float(criteria_weight or 0), float(effective_weight or 0), bool(enabled), what_to_check or "", when_to_check or "", good_example or "", bad_example or "", scoring_method or "", ts],
    )
    con.close()
    return fid

def update_rule(framework_id, **kwargs):
    con = connect()
    fields = []
    values = []
    for k in ["section_name","criteria_name","section_weight","criteria_weight","effective_weight","enabled","what_to_check","when_to_check","good_example","bad_example","scoring_method"]:
        if k in kwargs and kwargs[k] is not None:
            fields.append(f"{k} = ?")
            v = kwargs[k]
            if k in ["section_weight","criteria_weight","effective_weight"]:
                v = float(v)
            if k == "enabled":
                v = bool(v)
            values.append(v)
    values.append(datetime.utcnow())
    fields.append("updated_at = ?")
    values.append(framework_id)
    sql = "UPDATE qsdd_framework SET " + ", ".join(fields) + " WHERE framework_id = ?"
    con.execute(sql, values)
    con.close()
    return True

def delete_rule(framework_id):
    con = connect()
    con.execute("DELETE FROM qsdd_framework WHERE framework_id = ?", [framework_id])
    con.close()
    return True
