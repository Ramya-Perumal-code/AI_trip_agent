import json
import os
from dotenv import load_dotenv
from groq import Groq
from tool_calls import search_rag, duckduckgo_search

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def is_relevant(query: str, attraction_name: str) -> bool:
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
        rag_results = search_rag(query, k=3)
        valid_rag_results = []
        for doc, score in rag_results:
            attr_name = doc.metadata.get("Attraction_name", "")
            if score >= 0.5 and is_relevant(query, attr_name):
                valid_rag_results.append(f"--- RAG Result (Score: {score:.2f}) ---\n{doc.page_content}")
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

    system_prompt = "You are an expert travel assistant. Provide accurate, comprehensive answers based ONLY on the provided information. Use Markdown."
    user_content = f"Query: {query}\n\nRAG:\n{rag_info}\n\nAdditional:\n{additional_info}\n\nWeb:\n{web_info}"

    if client:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0
        )
        return completion.choices[0].message.content
    return "Groq API Key missing."

def AdditionalInfoAgent(query: str) -> str:
    # Simplified version for size reduction
    rag_results = search_rag(query, k=2)
    raw_info = "\n".join([d.page_content for d, s in rag_results])
    
    if not raw_info: return "No specific additional information found."
    
    if client:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Summarize the following travel metadata into concise bullet points."},
                {"role": "user", "content": raw_info}
            ]
        )
        return completion.choices[0].message.content
    return raw_info

def OrchestrateAgent(query: str) -> str:
    supp_info = AdditionalInfoAgent(query)
    if "no specific additional information" in supp_info.lower(): supp_info = None
    return TravelResearchAgent(query, additional_info=supp_info)
