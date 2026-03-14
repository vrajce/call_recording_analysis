import argparse
from chat_backend import ask_text_to_sql, preview_result, connect, execute_sql


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=None)
    p.add_argument("--sql", default=None)
    p.add_argument("--query", default=None)
    args = p.parse_args()
    if args.sql:
        con = connect(args.db)
        cols, rows = execute_sql(con, args.sql)
        print(preview_result(cols, rows))
        return
    if not args.query:
        raise SystemExit(1)
    res = ask_text_to_sql(args.query, args.db)
    if res["sql"]:
        print(res["sql"])
        print(preview_result(res["columns"], res["rows"]))
    else:
        print(res["answer"])


if __name__ == "__main__":
    main()

