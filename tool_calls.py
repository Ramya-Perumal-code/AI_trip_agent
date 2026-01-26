from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from duckduckgo_search import DDGS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Lightweight Embedding Wrapper for HuggingFace Inference API ---
class HFInferenceEmbeddings:
    def __init__(self, api_key: str, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = requests.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        return response.json()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

#----------------------------CONFIGURATION----------------------------

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Hybrid Embeddings: Use Google or HuggingFace (Cloud) if keys are present, else fallback to local
if GOOGLE_API_KEY:
    print("🚀 Using Google Gemini Embeddings (Cloud)")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
elif HUGGINGFACE_API_KEY:
    print("🚀 Using HuggingFace Inference API Embeddings (Cloud)")
    embeddings = HFInferenceEmbeddings(api_key=HUGGINGFACE_API_KEY)
else:
    print("🏠 Using Local HuggingFace Embeddings")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    except ImportError:
        print("⚠️ Warning: No cloud keys found and local libraries missing. App will fail.")
        embeddings = None

if QDRANT_URL and QDRANT_API_KEY:
    print("🚀 Connecting to Qdrant Cloud")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    print("🏠 Using Local Qdrant Store")
    client = QdrantClient(path="trip_rag_name")


def search_rag(query: str = "San Diego Zoo Day Pass?", k: int = 1) -> list:
    if not embeddings:
        return []
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="trip_rag_name",
        embedding=embeddings,
    )
    results = vector_store.similarity_search_with_score(query, k=k)
    return results

def duckduckgo_search(query: str, max_results: int = 3) -> dict:
    try:
        print(f"🔍 [Web] Searching DuckDuckGo for: {query}")
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e),
            "results": []
        }

# GYG Fetcher Integration
try:
    from gyg_fetcher import search_tours, get_tour_details
except ImportError:
    def search_tours(*args, **kwargs): return []
    def get_tour_details(*args, **kwargs): return {}

def search_gyg_activity(query: str) -> str:
    try:
        print(f"🎫 [GYG] Searching for: {query}")
        results = search_tours(query, limit=1)
        if not results: return ""
        top_tour_id = results[0]["tour_id"]
        tour_data = get_tour_details(top_tour_id)
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
    except Exception as e:
        print(f"❌ GYG Search failed: {e}")
        return ""
