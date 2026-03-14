import duckdb

def main():
    con = duckdb.connect("call_quality.duckdb")
    ans = con.execute("SELECT * from call_summary limit 2")

    print(ans.fetchall())
    con.close()

if __name__ == "__main__":
    main()
