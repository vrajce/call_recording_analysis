
# etl/etl_pipeline.py
# Run: python etl/etl_pipeline.py
import json, uuid, os, duckdb, re
from datetime import datetime
from textblob import TextBlob

DB_PATH    = "database/call_quality.duckdb"
CALLS_PATH = "data/raw/Call Details 1/Call Details"
TRANS_PATH = "data/raw/Call Transcripts 1/Call Transcripts"

def normalize(text):
    return re.sub(r"[^\w\s]", "", str(text).lower())

def run_etl():
    con = duckdb.connect(DB_PATH)
    print("ETL Pipeline Starting...")

    call_files  = [f for f in os.listdir(CALLS_PATH) if f.endswith(".json")]
    loaded = 0

    for fname in sorted(call_files):
        with open(f"{CALLS_PATH}/{fname}", "r") as f:
            raw = json.load(f)
        if isinstance(raw, list): raw = raw[0]

        cid = raw.get("contactId")
        if not cid: continue

        exists = con.execute("SELECT 1 FROM calls WHERE contact_id=?", [cid]).fetchone()
        if exists: continue

        try:
            ts_str = raw.get("contactStart","")
            ts = datetime.fromisoformat(ts_str.replace("Z","+00:00")).replace(tzinfo=None)
        except:
            ts = datetime.now()

        con.execute("""
            INSERT OR IGNORE INTO calls VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [
            cid, raw.get("agentId"),
            raw.get("campaignName","Unknown"), raw.get("skillName","Unknown"),
            raw.get("teamName","Unknown"), raw.get("firstName",""),
            raw.get("lastName",""), str(raw.get("fromAddr","")),
            str(raw.get("toAddr","")), ts,
            float(raw.get("totalDurationSeconds",0)),
            float(raw.get("agentSeconds",0)),
            float(raw.get("inQueueSeconds",0)),
            float(raw.get("holdSeconds",0)),
            float(raw.get("ACWSeconds",0)),
            int(raw.get("holdCount",0)),
            bool(raw.get("abandoned",False)),
            bool(raw.get("isOutbound",False)),
            str(raw.get("serviceLevelFlag","0")),
            raw.get("state","Unknown"),
            raw.get("mediaTypeName","Call"),
            False, datetime.now()
        ])
        loaded += 1

    print(f"ETL Complete: {loaded} calls loaded")
    con.close()

if __name__ == "__main__":
    run_etl()
