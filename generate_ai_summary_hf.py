import os
import duckdb
import json
import re
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_nebius import ChatNebius
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Initialize your powerful LLM for structured extraction
llm = ChatNebius(
    model="meta-llama/Llama-3.3-70B-Instruct", 
    temperature=0  # 0 is crucial for strict JSON formatting
)

# The "Crazy Optimal" Prompt for Interleaved Data
extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Quality Assurance AI. 
Analyze the provided customer support transcript. The data is interleaved: all customer text is grouped, and all agent text is grouped.

Extract the insights and return ONLY a valid JSON object with the following exact keys:
{{
    "issue_category": "Short 1-3 word category (e.g., Hardware, Billing, Login)",
    "issue_description": "1 sentence explaining the customer's problem",
    "resolution": "1 sentence explaining how the agent solved it, or 'Unresolved'",
    "sentiment_agent": "Positive, Neutral, or Negative",
    "sentiment_customer": "Positive, Neutral, or Negative",
    "overall_score": "Integer from 1 to 10 evaluating the agent's performance",
    "key_moments": "1 bullet point of the most critical moment in the call",
    "ai_recot": "1 sentence recommendation for the agent to improve next time"
}}
"""),
    ("human", "Customer's Dialogue:\n{customer_text}\n\nAgent's Dialogue:\n{agent_text}")
])

chain = extraction_prompt | llm

def process_call_summaries():
    db_path = "call_quality.duckdb"
    con = duckdb.connect(db_path)
    
    # Fetch calls from transcripts that don't have a populated summary yet.
    # We assume 'contact_id' in call_summary maps to 'call_id' in transcripts.
    calls = con.execute("""
        SELECT t.contact_id, t.agent_text, t.customer_text 
        FROM transcripts t
        LEFT JOIN call_summary c ON t.contact_id = c.contact_id
        WHERE c.contact_id IS NULL OR c.issue_category IS NULL
    """).fetchall()

    if not calls:
        print("All calls are already summarized in the call_summary table!")
        con.close()
        return

    print(f"Found {len(calls)} calls to analyze. Starting extraction...")

    for call_id, agent_text, customer_text in tqdm(calls, desc="Generating DB Summaries"):
        try:
            # 1. Ask the LLM to generate the JSON
            response = chain.invoke({
                "customer_text": customer_text[:3000], # Truncate to save tokens if needed
                "agent_text": agent_text[:3000]
            })
            
            content = getattr(response, "content", str(response))
            
            # 2. Extract JSON using regex (in case the LLM adds markdown backticks)
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                raise ValueError("LLM did not return valid JSON.")
            
            data = json.loads(json_match.group(0))
            
            con.execute("DELETE FROM call_summary WHERE contact_id = ?", [call_id])
            con.execute(
                "INSERT INTO call_summary (contact_id, issue_category, issue_description, resolution, sentiment_agent, sentiment_customer, overall_score, key_moments, ai_recommendation, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                [
                    call_id,
                    data.get("issue_category"),
                    data.get("issue_description"),
                    data.get("resolution"),
                    data.get("sentiment_agent"),
                    data.get("sentiment_customer"),
                    int(data.get("overall_score", 5)),
                    data.get("key_moments"),
                    data.get("ai_recot"),
                ],
            )
            
        except Exception as e:
            print(f"\nFailed to process Call ID {call_id}: {e}")

    print("\n✅ Analytics generation complete!")
    con.close()

if __name__ == "__main__":
    process_call_summaries()
