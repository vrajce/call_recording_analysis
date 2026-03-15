import duckdb
con = duckdb.connect("call_quality.duckdb")
row = con.execute("SELECT full_text FROM transcripts LIMIT 1").fetchone()
if row:
    print(f"Full Text sample (first 500 chars):\n{row[0][:500]}...")
else:
    print("No data found in transcripts table.")
con.close()
