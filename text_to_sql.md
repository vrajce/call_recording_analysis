# Epic: Build the Transcript RAG Chatbot (Nebius AI Edition)
**Goal:** Create a LangChain RAG chatbot that reads customer support transcripts from ChromaDB and answers questions in a Streamlit UI, powered entirely by Nebius AI Studio.

## Phase 1: Environment & Prerequisites
- [x] **Task 1.1:** Ensure the `call_quality.duckdb` file is available in your project directory.
- [x] **Task 1.2:** Create a `.env` file and set your API key: `NEBIUS_API_KEY=your_key_here`.
- [x] **Task 1.3:** Install required packages, including the official Nebius integration.
  - *Command:* `pip install langchain langchain-nebius langchain-community chromadb duckdb streamlit tiktoken`.

## Phase 2: Build the Vector Store (`build_chroma.py`)
*Note: This script runs once to convert the DuckDB text into a searchable vector database.*
- [x] **Task 2.1:** Create a script named `build_chroma.py`.
- [x] **Task 2.2:** Connect to DuckDB: `con = duckdb.connect("call_quality.duckdb")`.
- [x] **Task 2.3:** Fetch the transcripts using: `SELECT call_id, full_text FROM transcripts`.
- [x] **Task 2.4:** Import and initialize the Nebius embedding model: 
  - `from langchain_nebius import NebiusEmbeddings`.
  - `embeddings = NebiusEmbeddings(model="BAAI/bge-en-icl")`.
- [x] **Task 2.5:** Loop through the DuckDB results. Create a LangChain `Document` for each row where `page_content=full_text` and `metadata={"call_id": call_id}`.
- [x] **Task 2.6:** Save the documents to a local ChromaDB folder: `Chroma.from_documents(documents, embeddings, persist_directory="./vector_store")`.

## Phase 3: Build the RAG Logic (`chat_backend.py`)
- [x] **Task 3.1:** Create `chat_backend.py`. Import necessary LangChain modules (`Chroma`, `create_retrieval_chain`, `create_stuff_documents_chain`, `ChatPromptTemplate`) and the Nebius models (`ChatNebius`, `NebiusEmbeddings`).
- [x] **Task 3.2:** Load the Vector Store: `vectorstore = Chroma(persist_directory="./vector_store", embedding_function=NebiusEmbeddings(model="BAAI/bge-en-icl"))`.
- [x] **Task 3.3:** Create the retriever: `retriever = vectorstore.as_retriever(search_kwargs={"k": 3})`.
- [x] **Task 3.4:** Initialize the LLM using a powerful open-weights model hosted on Nebius: 
  - `llm = ChatNebius(model="meta-llama/Llama-3.3-70B-Instruct", temperature=0)`.
- [x] **Task 3.5:** Create a System Prompt: 
  - "You are a helpful AI Assistant for a customer support manager. Use the following retrieved transcript context to answer the user's question. If you don't know the answer based on the context, just say you don't know."
- [x] **Task 3.6:** Combine the LLM and prompt into a document chain, then combine that with the retriever to create the final `retrieval_chain`.
- [x] **Task 3.7:** Write a wrapper function `ask_bot(query: str) -> str` that invokes the chain and returns the answer.

## Phase 4: Streamlit UI Integration (`app.py`)
- [x] **Task 4.1:** In your Streamlit app, navigate to the Chatbot section.
- [x] **Task 4.2:** Import `ask_bot` from `chat_backend.py`.
- [x] **Task 4.3:** Initialize chat history: `if "messages" not in st.session_state: st.session_state.messages = []`.
- [x] **Task 4.4:** Render past messages using `st.chat_message`.
- [x] **Task 4.5:** Add the chat input: `if prompt := st.chat_input("Ask about call transcripts (e.g., 'Find calls with angry customers')..."):`.
- [x] **Task 4.6:** When a user submits a prompt:
  - Append to `st.session_state.messages`.
  - Display the user message.
  - Show `with st.spinner("Searching transcripts via Nebius AI..."):`
  - Call `response = ask_bot(prompt)`.
  - Display and append the assistant's response.