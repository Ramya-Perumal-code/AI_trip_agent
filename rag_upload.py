import json
import os
import shutil
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_core.documents import Document

load_dotenv()

#----------------------------IMPORTING LIBRARIES----------------------------

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Initialize client with cloud support and error handling for corrupted local metadata
if QDRANT_URL and QDRANT_API_KEY:
    print("🚀 Connecting to Qdrant Cloud for Upload")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    print("🏠 Using Local Qdrant Store for Upload")
    if os.path.exists("trip_rag_name"):
        try:
            # Try to initialize client - if it fails, the metadata is corrupted
            test_client = QdrantClient(path="trip_rag_name")
            test_client.get_collections()  # Try to access collections
            client = test_client
        except Exception as e:
            # Metadata is corrupted, delete and recreate
            print(f"Warning: Corrupted collection detected ({e}). Removing and recreating...")
            try:
                shutil.rmtree("trip_rag_name")
                print("Removed corrupted collection folder.")
            except Exception as cleanup_error:
                print(f"Could not remove corrupted folder: {cleanup_error}")
                raise
            client = QdrantClient(path="trip_rag_name")
    else:
        client = QdrantClient(path="trip_rag_name")

def upload_memory_rag(text: str):
    # client = QdrantClient(path="memory_rag")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="trip_rag_name",
        embedding=embeddings,
    )
    vector_store.add_texts(texts=[text])
    return "Memory RAG uploaded successfully"



def upload_rag():
    dataset_folder = "dataset_json"
    all_documents = []

    # Iterate over all JSON files in the dataset folder
    for filename in os.listdir(dataset_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(dataset_folder, filename)
            
            # Load JSON file directly without jq dependency
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue
            
            # Handle nested structure: check if data is under "data" -> "json" key (as seen in output3.json)
            if "data" in loaded_data and isinstance(loaded_data["data"], dict) and "json" in loaded_data["data"]:
                 json_data = loaded_data["data"]["json"]
                 full_metadata = loaded_data["data"].get("metadata", {})
            # Fallback for other structures (if any)
            elif "json" in loaded_data and isinstance(loaded_data["json"], dict):
                json_data = loaded_data["json"]
                full_metadata = loaded_data.get("metadata", {})
            else:
                json_data = loaded_data
                full_metadata = {}
            
            # Format the dictionary as a readable string
            content_parts = []
            
            if "Attraction_name" in json_data:
                content_parts.append(f"Attraction: {json_data['Attraction_name']}")
            
            if "Why visit" in json_data:
                why_visit = json_data["Why visit"]
                if isinstance(why_visit, list):
                    why_visit_strs = [str(v) for v in why_visit]
                    content_parts.append(f"Why visit: {', '.join(why_visit_strs)}")
                else:
                    content_parts.append(f"Why visit: {str(why_visit)}")
            
            if "What included" in json_data:
                included = json_data["What included"]
                if isinstance(included, list):
                    included_strs = [str(v) for v in included]
                    content_parts.append(f"What's included: {', '.join(included_strs)}")
                else:
                    content_parts.append(f"What's included: {str(included)}")
            
            if "What not included" in json_data:
                not_included = json_data["What not included"]
                if isinstance(not_included, list):
                    not_included_strs = [str(v) for v in not_included]
                    content_parts.append(f"What's not included: {', '.join(not_included_strs)}")
                else:
                    content_parts.append(f"What's not included: {str(not_included)}")
            
            if "Restrictions" in json_data:
                restrictions = json_data["Restrictions"]
                if isinstance(restrictions, list):
                    # Handle list of strings or other types
                    restriction_strs = [str(r) for r in restrictions]
                    content_parts.append(f"Restrictions: {', '.join(restriction_strs)}")
                else:
                    content_parts.append(f"Restrictions: {str(restrictions)}")
            
            if "Location" in json_data:
                location = json_data["Location"]
                if isinstance(location, list):
                    location_str = " ".join(str(loc) for loc in location)
                    content_parts.append(f"Location: {location_str}")
                else:
                    content_parts.append(f"Location: {str(location)}")
            
            if "User Rating" in json_data:
                content_parts.append(f"User Rating: {str(json_data['User Rating'])}")
            
            if "Duration" in json_data:
                content_parts.append(f"Duration: {str(json_data['Duration'])}")
            
            if "additional Information" in json_data:
                additional_Information = json_data["additional Information"]
                if isinstance(additional_Information, list):
                    additional_Information_str = " ".join(str(info) for info in additional_Information)
                    content_parts.append(f"additional Information: {additional_Information_str}")
                else:
                    content_parts.append(f"additional Information: {str(additional_Information)}")

            # Create a Document with string content and metadata
            page_content = "\n".join(content_parts)
            metadata = {"source": filename, "file_path": file_path}
            
            # Store the full json_data in metadata for easy access
            metadata["json"] = json.dumps(json_data) if json_data else ""
            
            # Add any additional fields from JSON as metadata (for backward compatibility)
            for key, value in json_data.items():
                if key not in ["Why visit", "What included", "What not included", 
                              "Restrictions", "Location", "User Rating", "Duration"]:
                    metadata[key] = str(value) if not isinstance(value, (dict, list)) else json.dumps(value)
            
            # Merge in full_metadata if it exists
            if full_metadata:
                for key, value in full_metadata.items():
                    if key not in metadata:  # Don't overwrite existing keys
                        metadata[key] = str(value) if not isinstance(value, (dict, list)) else json.dumps(value)
            
            doc = Document(page_content=page_content, metadata=metadata)
            all_documents.append(doc)

    # Check if collection exists and delete it if it does (to recreate with clean metadata)
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        if "trip_rag_name" in collection_names:
            print("Collection 'trip_rag_name' already exists. Deleting to recreate...")
            client.delete_collection("trip_rag_name")
    except Exception as e:
        print(f"Error checking/deleting collection: {e}")
        # Continue anyway - might be a new collection

    # Create the collection
    try:
        client.create_collection(
            collection_name="trip_rag_name",
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    except Exception as e:
        # If collection already exists, that's okay
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("Collection already exists, using existing collection.")
        else:
            raise

    vector_store = QdrantVectorStore(
        client=client,
        collection_name="trip_rag_name",
        embedding=embeddings,
    )

    if all_documents:
        vector_store.add_documents(documents=all_documents)
        return f"RAG uploaded successfully. Uploaded {len(all_documents)} documents."
    else:
        return "No documents found in the dataset_json folder."

print(upload_rag())