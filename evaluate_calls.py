import duckdb
import json
import re
import uuid
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_nebius import ChatNebius
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables (API keys)
load_dotenv()

# 1. Initialize the LLM (Temperature 0 is required for strict grading)
llm = ChatNebius(
    model="meta-llama/Llama-3.3-70B-Instruct", 
    temperature=0
)

# 2. Build the System Prompt
system_prompt = """You are an Expert Quality Assurance Auditor.
Your job is to evaluate a customer support transcript against our official QSDD Rubric.

### RUBRIC:
{rubric}

### INSTRUCTIONS:
1. Evaluate the transcript against EVERY criteria listed in the rubric.
2. Determine if the agent strictly passed (true) or failed (false) based on the 'what_to_check', 'good_example', and 'bad_example' rules.
3. Write a 1-sentence evidence-based reasoning quoting the transcript.
4. You MUST return ONLY a valid JSON array of objects. Do not include markdown formatting like ```json.

### REQUIRED JSON FORMAT:
[
    {{
        "section_name": "Section 1: Offer Assistance",
        "criteria_name": "Greeting",
        "passed": true,
        "reasoning": "Agent successfully said 'Thank you for calling Kenex Customer Service, my name is Alex'."
    }}
]
"""

eval_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "TRANSCRIPT TO EVALUATE:\n{transcript}")
])

chain = eval_prompt | llm

def calculate_and_store_scores():
    db_path = "call_quality.duckdb"
    con = duckdb.connect(db_path)
    
    print("📥 Fetching QSDD Framework Rubric...")
    
    # Fetch active rubric rules and their weights
    rubric_df = con.execute("""
        SELECT section_name, criteria_name, what_to_check, good_example, bad_example, effective_weight
        FROM qsdd_framework 
        WHERE enabled = true
    """).df()
    
    # Format rubric for the LLM Prompt
    rubric_text = ""
    for _, row in rubric_df.iterrows():
        rubric_text += f"Section: {row['section_name']}\n"
        rubric_text += f"Criteria: {row['criteria_name']}\n"
        rubric_text += f"Rule: {row['what_to_check']}\n"
        rubric_text += f"Pass Example: {row['good_example']}\n"
        rubric_text += f"Fail Example: {row['bad_example']}\n\n"

    print("📥 Fetching unscored transcripts...")
    
    # Fetch calls that haven't been scored yet
    calls_to_score = con.execute("""
        SELECT t.contact_id, c.agent_id, t.full_text 
        FROM transcripts t
        JOIN calls c ON t.contact_id = c.contact_id
        WHERE t.contact_id NOT IN (
            SELECT DISTINCT contact_id FROM quality_scores
        )
    """).fetchall()

    if not calls_to_score:
        print("✅ All transcripts have already been scored!")
        con.close()
        return

    print(f"🚀 Found {len(calls_to_score)} calls to evaluate. Starting AI Auditor...\n")

    for contact_id, agent_id, transcript in tqdm(calls_to_score, desc="Grading Calls"):
        try:
            # 1. Ask LLM to grade the transcript
            response = chain.invoke({
                "rubric": rubric_text,
                "transcript": transcript[:4000] # Safe truncation if transcript is massively long
            })
            
            content = getattr(response, "content", str(response))
            
            # 2. Extract JSON safely using regex
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if not json_match:
                raise ValueError("LLM did not return a valid JSON array.")
            
            evaluations = json.loads(json_match.group(0))
            
            # 3. Process each graded criteria
            for eval_item in evaluations:
                section_name = eval_item.get('section_name', '')
                criteria_name = eval_item.get('criteria_name', '')
                passed = bool(eval_item.get('passed', False))
                reasoning = eval_item.get('reasoning', '').replace("'", "''") # Escape quotes for SQL
                
                # --- THE MATH HAPPENS HERE ---
                # Look up the effective weight for this specific rule from the database
                weight_row = rubric_df[rubric_df['criteria_name'] == criteria_name]
                weight = float(weight_row['effective_weight'].values[0]) if not weight_row.empty else 0.0
                
                # Formula: If passed, they get the weight points. If failed, 0.
                calculated_score = weight if passed else 0.0
                
                # Generate a unique ID for this specific score row
                score_id = str(uuid.uuid4())

                # 4. Insert the final calculated row into quality_scores table
                con.execute(f"""
                    INSERT INTO quality_scores (
                        score_id, contact_id, agent_id, section_name, criteria_name, 
                        score, passed, reasoning, scored_by, evaluated_at
                    ) VALUES (
                        '{score_id}', '{contact_id}', '{agent_id}', '{section_name.replace("'", "''")}', '{criteria_name.replace("'", "''")}', 
                        {calculated_score}, {passed}, '{reasoning}', 'AI_Kenex_Auditor', CURRENT_TIMESTAMP
                    )
                """)
                
        except Exception as e:
            print(f"\n❌ Failed to process Call ID {contact_id}: {e}")

    print("\n✅ QA Scoring complete! Results saved to DuckDB.")
    con.close()

if __name__ == "__main__":
    calculate_and_store_scores()