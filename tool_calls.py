from qdrant_client import QdrantClient
from duckduckgo_search import DDGS
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

#----------------------------CONFIGURATION----------------------------

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# --- Direct Embedding Logic ---
def get_embeddings(texts: list[str]) -> list[list[float]]:
    if GOOGLE_API_KEY:
        # Use Google Gemini API directly
        url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:batchEmbedContents?key={GOOGLE_API_KEY}"
        payload = {
            "requests": [{"model": "models/embedding-001", "content": {"parts": [{"text": t}]}} for t in texts]
        }
        response = requests.post(url, json=payload)
        data = response.json()
        return [item["values"] for item in data["embeddings"]]
    
    elif HUGGINGFACE_API_KEY:
        # Use HuggingFace Inference API directly
        api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-mpnet-base-v2"
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        return response.json()
    
    return []

if QDRANT_URL and QDRANT_API_KEY:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    client = QdrantClient(path="trip_rag_name")

def search_rag(query: str, k: int = 3) -> list:
    try:
        query_vector = get_embeddings([query])[0]
        results = client.search(
            collection_name="trip_rag_name",
            query_vector=query_vector,
            limit=k,
            with_payload=True
        )
        # Format to match previous LangChain-like output for compatibility
        return [(type('Doc', (object,), {'page_content': r.payload.get('page_content', ''), 'metadata': r.payload})(), r.score) for r in results]
    except Exception as e:
        print(f"❌ RAG Search failed: {e}")
        return []

def duckduckgo_search(query: str, max_results: int = 3) -> dict:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e), "results": []}

# GYG Fetcher Integration
try:
    from gyg_fetcher import search_tours, get_tour_details
except ImportError:
    def search_tours(*args, **kwargs): return []
    def get_tour_details(*args, **kwargs): return {}

def search_gyg_activity(query: str) -> str:
    try:
        results = search_tours(query, limit=1)
        if not results: return ""
        tour_data = get_tour_details(results[0]["tour_id"])
        if not tour_data: return ""
        summary = [
            f"--- LIVE BOOKING DATA (GetYourGuide) ---",
            f"Title: {tour_data.get('Attraction_name')}",
            f"Rating: {tour_data.get('User Rating')}",
            f"Duration: {tour_data.get('Duration')}",
            f"Highlights: {', '.join(tour_data.get('Why visit', [])[:3])}",
            f"Inclusions: {', '.join(tour_data.get('What included', [])[:3])}",
            f"Price: Check availability for latest pricing.",
             "----------------------------------------"
        ]
        return "\n".join(summary)
    except Exception: return ""
