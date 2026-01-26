import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
from tool_calls import search_rag, duckduckgo_search

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Optional Ollama for local testing
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

def call_llm(system_prompt: str, user_content: str, temperature: float = 0) -> str:
    """Helper to call either Groq or Ollama."""
    if client:
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Groq Error: {e}")
    
    if HAS_OLLAMA:
        try:
            response = ollama.chat(
                model="qwen3:0.6b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            return response.message.content
        except Exception as e:
            print(f"❌ Ollama Error: {e}")
            
    return "No LLM provider (Groq/Ollama) available."

def is_relevant(query: str, attraction_name: str) -> bool:
    """Strict relevance guard to prevent false positives."""
    if not attraction_name: return False
    query_lower = query.lower()
    attraction_lower = attraction_name.lower()
    query_words = [w for w in query_lower.split() if len(w) > 3]
    for word in query_words:
        if word in attraction_lower: return True
    return attraction_lower in query_lower

def TravelResearchAgent(query: str, additional_info: str = None) -> str:
    print(f"🔍 [TravelResearchAgent] Processing: {query}")
    rag_info = ""
    try:
        rag_results = search_rag(query, k=5)
        RAG_SCORE_THRESHOLD = 0.5
        valid_rag_results = []
        
        for doc, score in rag_results:
            attr_name = doc.metadata.get("Attraction_name", "")
            if score >= RAG_SCORE_THRESHOLD and is_relevant(query, attr_name):
                doc_text = doc.page_content
                if 'data' in doc.metadata:
                    try:
                        data = doc.metadata['data']
                        if isinstance(data, str): data = json.loads(data)
                        if isinstance(data, dict) and 'markdown' in data:
                            doc_text = data['markdown']
                    except: pass
                valid_rag_results.append(f"--- RAG Result (Score: {score:.2f}) ---\n{doc_text}")
            elif score >= RAG_SCORE_THRESHOLD:
                print(f"⏩ Rejecting '{attr_name}' - Score OK ({score:.2f}) but not relevant.")
        
        rag_info = "\n\n".join(valid_rag_results)
    except Exception as e: print(f"❌ RAG Error: {e}")

    web_info = ""
    if not rag_info:
        try:
            web_results = duckduckgo_search(query, max_results=3)
            if web_results.get("status") == "success":
                web_texts = [f"--- Web Result ---\n{r.get('body', r.get('snippet', ''))}" for r in web_results.get("results", [])]
                web_info = "\n\n".join(web_texts)
        except Exception as e: print(f"❌ Web Error: {e}")

    system_prompt = (
        "You are an expert travel assistant. Provide accurate, comprehensive answers.\n"
        "CRITICAL: ONLY use provided information. DO NOT hallucinate.\n"
        "Structure your response with these sections:\n"
        "1. **Overview**: Name, location, description.\n"
        "2. **What is Included & Not Included**: Tickets, amenities, services.\n"
        "3. **Pricing & Tickets**: Fees, discounts, booking info.\n"
        "4. **Hours & Availability**: Operating hours, best times.\n"
        "5. **Restrictions & Requirements**: Age, accessibility, dress code.\n"
        "6. **Tips & Recommendations**: Best practices.\n"
        "Use Markdown. Begin directly with the information."
    )
    
    user_content = f"User Query: {query}\n\nRAG Info:\n{rag_info}\n\nAdditional Info:\n{additional_info}\n\nWeb Info:\n{web_info}"
    return call_llm(system_prompt, user_content)

def gather_additional_information(query: str, rag_results: list) -> str:
    """Complex metadata extraction logic from RAG/Web."""
    additional_info = set()
    RAG_SCORE_THRESHOLD = 0.5
    
    if rag_results:
        filtered = [r for r in rag_results if r[1] >= RAG_SCORE_THRESHOLD and is_relevant(query, r[0].metadata.get("Attraction_name", ""))]
        if filtered:
            primary_attr = filtered[0][0].metadata.get("Attraction_name")
            for doc, score in filtered:
                meta = doc.metadata
                if primary_attr and meta.get("Attraction_name") != primary_attr: continue
                
                info_data = meta.get("additional Information") or meta.get("json", {}).get("additional Information")
                if info_data:
                    try:
                        if isinstance(info_data, str) and info_data.strip().startswith('['):
                            parsed = json.loads(info_data)
                            for p in parsed: additional_info.add(str(p))
                        elif isinstance(info_data, list):
                            for i in info_data: additional_info.add(str(i))
                        else: additional_info.add(str(info_data))
                    except: additional_info.add(str(info_data))

    if not additional_info:
        try:
            web_res = duckduckgo_search(f"{query} additional tourist information details", max_results=2)
            if web_res.get("status") == "success":
                for r in web_res.get("results", []):
                    additional_info.add(f"Web: {r.get('body', r.get('snippet', ''))}")
        except: pass

    return "\n".join([f"- {item}" for item in sorted(list(additional_info))])

def AdditionalInfoAgent(query: str) -> str:
    print(f"🔍 [AdditionalInfoAgent] Gathering for: {query}")
    try:
        rag_results = search_rag(query, k=3)
        raw_info = gather_additional_information(query, rag_results)
        
        if not raw_info or "no specific additional info" in raw_info.lower():
            return "No specific additional information found."

        system_prompt = (
            "You are a 'Travel Metadata Expert'. Turn raw information into a concise, professional "
            "list of supplementary details. Group similar points, remove duplicates, and use Markdown."
        )
        user_content = f"Attraction Query: {query}\n\nRaw Metadata:\n{raw_info}"
        return call_llm(system_prompt, user_content)
    except Exception as e:
        return f"Error gathering info: {str(e)}"

def OrchestrateAgent(query: str) -> str:
    supp_info = AdditionalInfoAgent(query)
    if not supp_info or "no specific additional information" in supp_info.lower():
        supp_info = None
    return TravelResearchAgent(query, additional_info=supp_info)
