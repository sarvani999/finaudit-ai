# app/rag.py
import os
from dotenv import load_dotenv
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_postgres.vectorstores import PGVector

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = "enterprise_financial_policies"

# Free, fast, local embedding model (runs directly on your CPU without API key)
embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def get_vector_store() -> PGVector:
    """Returns the PGVector vectorstore instance connected to Neon PostgreSQL."""
    return PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
    )

def retrieve_relevant_policies(query: str, k: int = 2) -> str:
    """Retrieves top-k relevant policy clauses based on invoice context."""
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=k)
    
    if not results:
        return "No specific policy clause matched."
    
    formatted_policies = []
    for doc in results:
        formatted_policies.append(f"--- Policy Rule ---\n{doc.page_content.strip()}")
        
    return "\n\n".join(formatted_policies)