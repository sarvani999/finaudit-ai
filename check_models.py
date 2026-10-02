# check_models.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Checking available models for your API key...")
try:
    models = [m.name for m in client.models.list() if "generateContent" in m.supported_actions]
    print(f"\nFound {len(models)} models! Recommended models for you:")
    for m in models:
        if "flash" in m or "pro" in m:
            print(f" -> {m}")
except Exception as e:
    print(f"Error: {e}")