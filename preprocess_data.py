import duckdb

def get_formatted_transcripts():
    """
    Connect to DuckDB, fetch agent_text and customer_text, 
    and format them as dialogue.
    """
    con = duckdb.connect("call_quality.duckdb")
    
    # Fetch agent_text and customer_text
    print("Fetching transcripts for preprocessing...")
    query = "SELECT contact_id, agent_text, customer_text FROM transcripts"
    results = con.execute(query).fetchall()
    
    formatted_data = []
    for contact_id, agent_text, customer_text in results:
        # Task 1.2: Format as dialogue
        # AGENT: [text] \n CUSTOMER: [text]
        # We handle potential None values
        agent_str = agent_text if agent_text else ""
        customer_str = customer_text if customer_text else ""
        
        formatted_text = f"AGENT: {agent_str}\n\nCUSTOMER: {customer_str}"
        
        formatted_data.append({
            "contact_id": contact_id,
            "formatted_text": formatted_text
        })
    
    con.close()
    print(f"Preprocessed {len(formatted_data)} transcripts.")
    return formatted_data

if __name__ == "__main__":
    # Test the preprocessing
    data = get_formatted_transcripts()
    if data:
        print("\n--- Example Preprocessed Transcript (First 200 chars) ---")
        print(data[0]["formatted_text"][:200] + "...")
