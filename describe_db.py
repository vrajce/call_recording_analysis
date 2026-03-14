import duckdb
con = duckdb.connect("call_quality.duckdb")
print(con.execute("DESCRIBE transcripts;").fetchall())
con.close()
