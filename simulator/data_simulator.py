
# simulator/data_simulator.py
# Run: python simulator/data_simulator.py
import random, time, uuid, duckdb, json, re
from datetime import datetime, timedelta
from textblob import TextBlob

DB_PATH = "database/call_quality.duckdb"

AGENTS = [
    {"id":28787456,"name":"Alex Morgan",  "team":"Dedicated - Douglas Elliman","skill":"DE.SKL.PHN.EN"},
    {"id":28787457,"name":"Sarah Johnson","team":"Shared Services",             "skill":"UI.SKL.PHN.EN"},
    {"id":28787458,"name":"Mike Torres",  "team":"Tech Support",                "skill":"UI.SKL.PHN.ES"},
    {"id":28787459,"name":"Emily Chen",   "team":"Tech Support",                "skill":"UI.SKL.PHN.EN"},
    {"id":28787460,"name":"James Patel",  "team":"Billing Support",             "skill":"UI.SKL.PHN.EN"},
]

def run_simulator(batches=999, calls_per_batch=3, interval=60):
    print(f"Simulator: {batches} batches, {calls_per_batch} calls/batch, {interval}s interval")
    counter = 0
    for batch in range(batches):
        for _ in range(calls_per_batch):
            counter += 1
            agent    = random.choice(AGENTS)
            is_good  = random.random() > 0.30
            now      = datetime.now()
            cid      = int(now.timestamp()*100) + counter
            dur      = random.uniform(300, 3000)

            agent_text = (
                f"Thank you for calling Customer Service Desk, my name is {agent['name']}. "
                f"May I have your first and last name? And a callback number please? "
                f"I completely understand. Let me help you resolve this right away. "
                f"Is there anything else I can help you with today? "
                f"Thank you for calling, have a great day. Goodbye."
                if is_good else "Hello support. What is the issue. Okay bye."
            )
            cust_text = (
                "Hi I need help with my account access issue. "
                "Thank you that really helped. Have a good day."
                if is_good else "Hi I have a problem. That did not help. Goodbye."
            )

            con = duckdb.connect(DB_PATH)
            try:
                ts = now - timedelta(minutes=random.randint(1,30))
                aw = len(agent_text.split())
                cw = len(cust_text.split())
                tr = round(aw/(aw+cw),3)

                con.execute("""
                    INSERT OR IGNORE INTO calls VALUES
                    (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, [cid, agent["id"], "Simulated Campaign",
                      agent["skill"], agent["team"],
                      "Test","User","5550000000","2246660395",
                      ts, dur, dur*0.7, random.uniform(5,60),
                      random.uniform(0,120), random.uniform(5,30),
                      random.randint(0,2), False, False,
                      "1" if random.random()>0.2 else "0",
                      "EndContact","Call", True, datetime.now()])

                con.execute("""
                    INSERT OR IGNORE INTO transcripts VALUES (?,?,?,?,?,?,?,?,?)
                """, [str(uuid.uuid4()), cid, agent_text, cust_text,
                      f"{agent_text} {cust_text}", aw, cw, tr, datetime.now()])

                print(f"  [Batch {batch+1}] Added call {cid} | {'GOOD' if is_good else 'BAD'}")
            finally:
                con.close()

        if batch < batches-1:
            time.sleep(interval)

if __name__ == "__main__":
    run_simulator(batches=3, calls_per_batch=3, interval=60)
