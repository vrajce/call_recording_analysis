import duckdb
import os
from dotenv import load_dotenv
from langchain_nebius import NebiusEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

def build_vector_store():
    # Connect to DuckDB
    con = duckdb.connect("call_quality.duckdb")
    
    # Fetch the transcripts (using contact_id instead of call_id as per schema)
    print("Fetching transcripts from DuckDB...")
    results = con.execute("SELECT contact_id, full_text FROM transcripts").fetchall()
    
    # Initialize Nebius embedding model
    print("Initializing Nebius embeddings...")
    embeddings = NebiusEmbeddings(model="BAAI/bge-en-icl")
    
    # Create LangChain Documents
    documents = []
    for contact_id, full_text in results:
        doc = Document(
            page_content=full_text,
            metadata={"call_id": contact_id}
        )
        documents.append(doc)
    
    # Save the documents to a local ChromaDB folder
    print(f"Persisting {len(documents)} documents to ChromaDB at ./vector_store...")
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./vector_store"
    )
    
    print("Vector store built successfully!")
    con.close()

if __name__ == "__main__":
    build_vector_store()
