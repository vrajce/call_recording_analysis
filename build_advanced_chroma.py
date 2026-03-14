import os 
import time 
from tqdm import tqdm # For the progress bar 
from dotenv import load_dotenv 
from langchain_nebius import NebiusEmbeddings 
from langchain_community.vectorstores import Chroma 
from langchain_classic.retrievers import ParentDocumentRetriever 
from langchain_classic.storage import LocalFileStore, create_kv_docstore
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_core.documents import Document 
from preprocess_data import get_formatted_transcripts 

load_dotenv() 

def build_advanced_vector_store(): 
    # 1. Fetch data 
    data = get_formatted_transcripts() 
    documents = [ 
        Document(page_content=e["formatted_text"], metadata={"call_id": e["contact_id"]}) 
        for e in data 
    ] 
    
    # 2. Initialize Embeddings (Verify your API key is working) 
    embeddings = NebiusEmbeddings(model="BAAI/bge-en-icl") 
    
    # 3. Setup Splitters 
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000) 
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50) 
    
    # 4. Setup Persistent Storage (Fixes the "lost on restart" issue) 
    # Store the parent documents on disk so you don't have to re-embed every time 
    if not os.path.exists("./parent_records"):
        os.makedirs("./parent_records")
    fs = LocalFileStore("./parent_records") 
    store = create_kv_docstore(fs) 
    
    vectorstore = Chroma( 
        collection_name="advanced_transcripts", 
        embedding_function=embeddings, 
        persist_directory="./advanced_vector_store" 
    ) 
    
    # 5. Initialize Retriever 
    retriever = ParentDocumentRetriever( 
        vectorstore=vectorstore, 
        docstore=store, 
        child_splitter=child_splitter, 
        parent_splitter=parent_splitter, 
    ) 
    
    # 6. Run Ingestion with Progress Bar 
    print(f"Starting ingestion of {len(documents)} transcripts...") 
    start_time = time.time() 
    
    # We add documents in batches to avoid timing out the API 
    batch_size = 5 
    for i in tqdm(range(0, len(documents), batch_size), desc="Embedding Batches"): 
        batch = documents[i : i + batch_size] 
        retriever.add_documents(batch, ids=None) 
    
    total_time = time.time() - start_time 
    print(f"Done! Advanced RAG built in {total_time:.2f} seconds.") 
    return retriever 

if __name__ == "__main__": 
    build_advanced_vector_store()
