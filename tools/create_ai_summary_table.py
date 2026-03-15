import duckdb
from datetime import datetime

def main():
    con = duckdb.connect("call_quality.duckdb")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_summary (
            contact_id BIGINT,
            agent_id BIGINT,
            summary VARCHAR,
            strengths VARCHAR,
            improvements VARCHAR,
            failed_criteria VARCHAR,
            model_name VARCHAR,
            version INTEGER,
            created_at TIMESTAMP
        )
        """
    )
    con.close()
    print("ai_summary table ready")

if __name__ == "__main__":
    main()
