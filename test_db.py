import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env file
load_dotenv()

database_url = os.getenv("DATABASE_URL")
print(f"Connecting to database...")

try:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        # 1. Test basic connection
        result = connection.execute(text("SELECT version();")).fetchone()
        print("Connected successfully to PostgreSQL!")
        print(f"Version: {result[0][:35]}...")

        # 2. Enable pgvector extension
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit()
        print("pgvector extension enabled successfully!")

except Exception as e:
    print(f"Connection failed: {e}")