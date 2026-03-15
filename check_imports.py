try:
    from langchain.chains import create_retrieval_chain
    print("Successfully imported from langchain.chains")
except ImportError as e:
    print(f"Failed to import from langchain.chains: {e}")

try:
    import langchain.chains
    print(f"langchain.chains attributes: {dir(langchain.chains)}")
except Exception as e:
    print(f"Failed to explore langchain.chains: {e}")
