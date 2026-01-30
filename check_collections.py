from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if QDRANT_URL and QDRANT_API_KEY:
    print(f"Checking Qdrant Cloud: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    print("Checking Local Qdrant")
    client = QdrantClient(path="trip_rag_name")

try:
    collections = client.get_collections()
    print("Collections found:")
    for col in collections.collections:
        print(f" - {col.name}")
except Exception as e:
    print(f"Error: {e}")
