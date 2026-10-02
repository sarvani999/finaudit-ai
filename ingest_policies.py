# ingest_policies.py
import os
from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter
from app.rag import get_vector_store

load_dotenv()

def ingest_governance_policies():
    policy_path = "data/policies/procurement_governance.md"
    
    if not os.path.exists(policy_path):
        print(f"Error: {policy_path} not found!")
        return

    print("Reading procurement governance policy...")
    with open(policy_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    splits = markdown_splitter.split_text(markdown_content)

    print(f"Divided policy into {len(splits)} semantic chunks.")

    vector_store = get_vector_store()
    print("Generating OpenAI embeddings and storing into Neon pgvector...")
    vector_store.add_documents(splits)
    print("All enterprise policies successfully indexed into pgvector!")

if __name__ == "__main__":
    ingest_governance_policies()