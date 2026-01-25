from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_community.tools import DuckDuckGoSearchRun
import json
import os
from dotenv import load_dotenv
import atexit

load_dotenv()

# Ensure ddgs is available for DuckDuckGoSearchRun
try:
    import ddgs
except ImportError:
    print("Warning: ddgs package not found. DuckDuckGo search may not work.")
    print("Install it with: pip install ddgs")

# LOCK_PATH = os.path.join(os.path.dirname(__file__), ".trip_rag.lock")
# try:
#     _lock_fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_RDWR)
#     os.write(_lock_fd, str(os.getpid()).encode())
# except FileExistsError as exc:
#     raise RuntimeError(
#         "trip_rag store is already in use by another Python process. "
#         "Close the other process before launching this script."
#     ) from exc


# def _release_lock() -> None:
#     """Release the lock file so another process can access the store."""
#     if "_lock_fd" in globals():
#         try:
#             os.close(_lock_fd)
#         except OSError:
#             pass
#     try:
#         os.remove(LOCK_PATH)
#     except FileNotFoundError:
#         pass


# atexit.register(_release_lock)

#----------------------------IMPORTING LIBRARIES----------------------------

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Use HuggingFace Embeddings (CPU) for both Local and Cloud for now
# Groq doesn't support embeddings yet, and HF is free/reliable
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

if QDRANT_URL and QDRANT_API_KEY:
    print("🚀 Connecting to Qdrant Cloud")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    print("🏠 Using Local Qdrant Store")
    client = QdrantClient(path="trip_rag_name")


def search_rag(query: str = "San Diego Zoo Day Pass?", k: int = 1) -> list:
    """
    Search for recipes in the RAG vector store.
    
    Args:
        query: The search query string
        k: Number of results to return
        
    Returns:
        list: List of search results with scores
    """
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="trip_rag_name",
        embedding=embeddings,
    )

    results = vector_store.similarity_search_with_score(query, k=k)
    return results

def duckduckgo_search(query: str, max_results: int = 3) -> dict:
    """
    Performs a DuckDuckGo web search using LangChain's DuckDuckGoSearch tool.
    This is a privacy-focused search API designed for LLM Agents.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 3)

    Returns:
        dict: Dictionary containing search results with 'status' and 'results' keys.
              Results include title, link, and snippet for each search result.
    """
    try:
        # Initialize DuckDuckGoSearch tool with max_results
        search_tool = DuckDuckGoSearchRun(max_results=max_results)
        
        # Invoke the search tool
        search_results = search_tool.invoke(query)
        
        # Parse the results if they're in string format
        if isinstance(search_results, str):
            # Try to parse as JSON if it's JSON-formatted
            try:
                parsed_results = json.loads(search_results)
            except json.JSONDecodeError:
                # If not JSON, return as formatted string
                parsed_results = search_results
        else:
            parsed_results = search_results
        
        return {
            "status": "success",
            "query": query,
            "results": parsed_results,
            "count": max_results
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e),
            "results": []
        }


# Example usage:
if __name__ == "__main__":
    query = "tell me about SUMMIT One Vanderbilt Tickets?"
    # results = search_rag(query)
    # print("results from search_rag",results)
    
    # # Convert Document objects to JSON-serializable format
    # serializable_results = [
    #     {
    #         "content": doc.page_content,
    #         "score": float(score),
    #         "metadata": doc.metadata
    #     }
    #     for doc, score in results
    # ]
    
    # print("RAG Search Results:")
    # print(json.dumps(serializable_results, indent=2))
    # if len(serializable_results) > 0:
    #     print("serializable_results[0]",serializable_results[0]['content'])
    #     print("serializable_results[0]",serializable_results[0]['metadata'])
    # if len(serializable_results) > 1:
    #     print("serializable_results[1]",serializable_results[1]['content'])
    #     print("serializable_results[1]",serializable_results[1]['metadata'])
    # if len(serializable_results) > 2:
    #     print("serializable_results[2]",serializable_results[2]['content'])
    #     print("serializable_results[2]",serializable_results[2]['metadata'])
    
    # Uncomment to test DuckDuckGo search:
    # web_results = duckduckgo_search(query, max_results=3)
    # print("\nDuckDuckGo Search Results:")
    # print(json.dumps(web_results, indent=2))

try:
    from gyg_fetcher import search_tours, get_tour_details
except ImportError:
    print("Warning: gyg_fetcher not found.")
    def search_tours(*args, **kwargs): return []
    def get_tour_details(*args, **kwargs): return {}

def search_gyg_activity(query: str) -> str:
    """
    Searches for activities using the GetYourGuide Fetcher (Mock/Real).
    Returns a formatted string of the top result's details.
    """
    try:
        # 1. Search
        print(f"🎫 [GYG] Searching for: {query}")
        results = search_tours(query, limit=1)
        
        if not results:
            return ""

        # 2. Get Details of top result
        top_tour_id = results[0]["tour_id"]
        tour_data = get_tour_details(top_tour_id)
        
        # 3. Format as a readable string for the LLM
        if not tour_data:
             return ""
             
        # Create a compact summary
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

