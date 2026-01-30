import ollama
import json
from tool_calls import search_rag, duckduckgo_search

def is_relevant(query: str, attraction_name: str) -> bool:
    """
    Checks if the attraction name is actually relevant to the user query.
    Prevents false positives like Madame Tussauds appearing for Taj Mahal.
    """
    if not attraction_name:
        return False
        
    query_lower = query.lower()
    attraction_lower = attraction_name.lower()
    
    # Split query into meaningful words (length > 3)
    query_words = [w for w in query_lower.split() if len(w) > 3]
    
    # If any specific name from the query appears in the attraction name, it's a good sign
    for word in query_words:
        if word in attraction_lower:
            return True
            
    # Also check if the attraction name appears in the query
    if attraction_lower in query_lower:
        return True
        
    return False

def TravelResearchAgent(query: str, additional_info: str = None) -> str:
    """
    Research agent that gathers information from RAG and Web to answer travel queries.
    It can also take optional pre-gathered additional information to synthesize into the final response.
    """

    print(f"🔍 [TravelResearchAgent] Processing query: {query}")
    
    # 1. Search RAG
    rag_info = ""
    try:
        print("🔍 Searching RAG...")
        rag_results = search_rag(query, k=3)
        
        # Filter results by score AND relevance
        RAG_SCORE_THRESHOLD = 0.5
        valid_rag_results = []
        
        for doc, score in rag_results:
            meta = getattr(doc, 'metadata', {})
            attraction_name = meta.get("Attraction_name", "")
            
            if score >= RAG_SCORE_THRESHOLD and is_relevant(query, attraction_name):
                valid_rag_results.append((doc, score))
            elif score >= RAG_SCORE_THRESHOLD:
                print(f"⏩ Rejecting '{attraction_name}' - Score OK ({score:.2f}) but not relevant to query.")
        
        if valid_rag_results:
            rag_texts = []
            for doc, score in valid_rag_results:
                content = getattr(doc, 'page_content', str(doc))
                rag_texts.append(f"--- RAG Result (Score: {score:.2f}) ---\n{content}")
            
            rag_info = "\n\n".join(rag_texts)
            print("RAG info:", rag_info)
            print(f"✅ Found {len(valid_rag_results)} relevant RAG results (Score >= {RAG_SCORE_THRESHOLD}).")
        else:
            if rag_results:
                print(f"⚠️ RAG results found but all below threshold {RAG_SCORE_THRESHOLD} (Max score: {max(r[1] for r in rag_results):.2f}).")
            else:
                print("⚠️ No RAG results found.")
    except Exception as e:
        print(f"❌ RAG Search failed: {e}")

    # 3. Gather Additional Information
    # additional_data = gather_additional_information(query, valid_rag_results if 'valid_rag_results' in locals() else [])

    # 3. Search Web (Fallback if RAG is empty)
    web_info = ""
    if not rag_info:
        try:
            print("🔍 RAG results missing. Searching Web...")
            web_results = duckduckgo_search(query, max_results=3)
            if web_results and web_results.get("status") == "success":
                results = web_results.get("results", [])
                web_texts = []
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            web_texts.append(f"--- Web Result: {item.get('title', 'No Title')} ---\n{item.get('body', item.get('snippet', ''))}")
                        else:
                            web_texts.append(str(item))
                elif isinstance(results, str):
                    web_texts.append(results)
                
                web_info = "\n\n".join(web_texts)
                print("✅ Web search completed.")
            else:
                print("⚠️ Web search returned no results.")
        except Exception as e:
            print(f"❌ Web Search failed: {e}")
    else:
        print("ℹ️ RAG results found. Skipping Web Search.")

    # 3. Synthesize
    print("📝 Synthesizing response...")
    
    system_prompt = (
        "You are an expert travel assistant agent whose job is to provide accurate, comprehensive answers "
        "about tourist attractions, activities, and travel destinations.\n\n"
        "CRITICAL: You MUST ONLY provide information that is explicitly found in the gathered information. "
        "DO NOT make up, guess, or hallucinate any information. If information is not available, say so clearly.\n\n"
        "You have access to these tools:\n"
        "- search_rag: Search a local, curated knowledge base of travel and attraction data\n"
        "- duckduckgo_search: Search the web for up-to-date or missing information\n\n"
        "Instructions:\n"
        "1. When gathering missing information, always try search_rag first.\n"
        "2. If search_rag does NOT provide the required information (it's missing or insufficient), THEN and only then use duckduckgo_search to search the web for what is missing, including specifically ticketing/pricing details if they are unavailable in RAG.\n"
        "3. IMPORTANT: The information you receive will be about the SPECIFIC attraction/activity mentioned in the user query. "
        "You MUST ensure your response matches the EXACT attraction/activity name from the user query. "
        "If the gathered information is about a different attraction, you MUST NOT use it. Only use information that matches the user's query.\n"
        "4. Make sure to collect and present ONLY information that is found in the gathered data:\n"
        "   1. **Basic Information**: Name, location, description, and overview (MUST match the user's query)\n"
        "   2. **What is Included & Not Included**: List what the attraction/activity/tour offers (tickets, amenities, services, features) and what it DOES NOT include (such as meals, transport, extras, tips, etc.)\n"
        "   3. **Pricing & Tickets**: Admission fees, ticket prices, discounts, package deals, booking information. If this cannot be found in RAG, use duckduckgo_search to look it up and include it.\n"
        "   4. **Hours & Availability**: Operating hours, seasonal availability, best times to visit, peak hours\n"
        "   5. **Reviews & Ratings**: User reviews, ratings (TripAdvisor, Google, Yelp), praises, complaints, satisfaction\n"
        "   6. **Restrictions & Requirements**: Age/weight restrictions, accessibility, dress codes, health, reservation needs\n"
        "   7. **What to Expect**: Activities, exhibits, shows, experiences, visit duration, highlights\n"
        "   8. **Practical Info**: Parking, transportation, amenities, facilities\n"
        "   9. **Tips & Recommendations**: Best practices, what to bring/avoid, strategies\n"
        "  10. **Current Updates**: Changes, closures, promotions\n"
        "  11. **Additional Information**: Any other relevant details found.\n"
        "5. Always try to fill in ALL key gaps, especially for reviews, ratings, restrictions, what is included/not included, and pricing/ticketing (make a follow-up duckduckgo_search if any are missing after search_rag).\n"
        "6. Once you have comprehensive information, synthesize everything into a clear, well-structured, user-friendly answer in MARKDOWN format.\n"
        "7. Do NOT include tool call syntax (like <search_rag> or <duckduckgo_search>) in your response.\n"
        "8. Do NOT include phrases like 'Final Answer', 'Final Response', 'Answer:', or similar labels - just provide the information directly.\n"
        "9. Organize content logically in sections with markdown headings/lists. Highlight important restrictions and included/not included items prominently.\n"
        "10. Begin directly with the information—no introductions or labels.\n"
        "11. VERIFY: Before responding, check that the attraction name in your response matches the user's query. If it doesn't match, do not provide that information."
    )
    
    user_content = (
        f"User Query: {query}\n\n"
        f"### RAG Information:\n{rag_info if rag_info else 'No RAG info available.'}\n\n"
        f"### Additional Details (Metadata):\n{additional_info if additional_info else 'No specific additional details provided.'}\n\n"
        f"### Web Information:\n{web_info if web_info else 'No Web info available.'}\n\n"
        "Please provide a comprehensive, unified answer that incorporates the additional details into the main narrative."
    )

    try:
        response = ollama.chat(
            model="qwen3:0.6b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"Error generating response: {e}"

def gather_additional_information(query: str, rag_results: list) -> str:
    """
    Extracts 'additional Information' from RAG results if present.
    Filters by the most relevant attraction name to avoid data mixing.
    Fallback: Uses DuckDuckGo search if not found in RAG.
    """
    additional_info = set() # Use a set to prevent duplicates
    primary_attraction = None
    
    # 1. Try to get from RAG metadata
    if rag_results:
        # Filter RAG results by score and relevance BEFORE processing
        RAG_SCORE_THRESHOLD = 0.5
        filtered_results = []
        for doc, score in rag_results:
            meta = getattr(doc, 'metadata', {})
            attr_name = meta.get("Attraction_name", "")
            if score >= RAG_SCORE_THRESHOLD and is_relevant(query, attr_name):
                filtered_results.append((doc, score))
            elif score >= RAG_SCORE_THRESHOLD:
                print(f"⏩ [GatherInfo] Skipping '{attr_name}' as it doesn't match query.")

        if filtered_results:
            print("🔍 Checking RAG for 'additional Information'...")
            # Use the most relevant (top) attraction as the anchor
            first_doc, _ = filtered_results[0]
            primary_attraction = getattr(first_doc, 'metadata', {}).get("Attraction_name")
            if primary_attraction:
                print(f"🎯 Target Attraction: {primary_attraction}")

            for doc, score in filtered_results:
                # Check metadata
                meta = getattr(doc, 'metadata', {})
                current_attraction = meta.get("Attraction_name")
                
                # Double check to ensure we don't mix info from different attractions
                if primary_attraction and current_attraction and current_attraction != primary_attraction:
                    continue

                # In rag_upload.py, it's stored as "additional Information"
            info_data = meta.get("additional Information")
            
            if info_data:
                # It might be in JSON format or raw string
                try:
                    if isinstance(info_data, str):
                        # Attempt to parse as JSON list
                        if info_data.strip().startswith('['):
                            parsed = json.loads(info_data)
                            if isinstance(parsed, list):
                                for p in parsed:
                                    additional_info.add(str(p))
                            else:
                                additional_info.add(str(parsed))
                        else:
                             additional_info.add(info_data)
                    elif isinstance(info_data, list):
                        for i in info_data:
                            additional_info.add(str(i))
                except Exception:
                    additional_info.add(str(info_data))

    # 2. If no additional info found in RAG, search specifically for it (Fallback)
    if not additional_info:
        # Only search if we haven't found it in RAG
        try:
            print("🔍 'additional Information' specific field not found in RAG. Searching Web specifically for it...")
            web_res = duckduckgo_search(f"{query} additional tourist information details", max_results=2)
            if web_res and web_res.get("status") == "success":
                 results = web_res.get("results", [])
                 if isinstance(results, list):
                     for r in results:
                         if isinstance(r, dict):
                             additional_info.add(f"Web: {r.get('body', r.get('snippet', ''))}")
                         else:
                            additional_info.add(f"Web: {str(r)}")
                 elif isinstance(results, str):
                     additional_info.add(f"Web: {results}")
            else:
                print("⚠️ Additional Info Web search returned no results.")
        except Exception as e:
            print(f"❌ Additional Info Web Search failed: {e}")
    else:
        print(f"✅ Found {len(additional_info)} unique 'additional Information' items in RAG.")
        print(list(additional_info))

    return "\n".join([f"- {item}" for item in sorted(list(additional_info))])

def AdditionalInfoAgent(query: str) -> str:
    """
    Standalone agent that gathers and synthesizes additional info using RAG/Web and LLM.
    """
    print(f"🔍 [AdditionalInfoAgent] Processing query: {query}")
    try:
        # 1. Gather raw data from RAG/Web
        rag_results = search_rag(query, k=3)
        raw_info = gather_additional_information(query, rag_results)
        
        if not raw_info or "no specific additional info found" in raw_info.lower():
            return "No specific additional information found."

        # 2. Synthesize using LLM
        print("📝 [AdditionalInfoAgent] Synthesizing metadata...")
        system_prompt = (
            "You are a 'Travel Metadata Expert'. Your job is to take raw, technical, or fragmented "
            "information about a tourist attraction and turn it into a concise, professional, and "
            "highly readable list of supplementary details for a traveler.\n\n"
            "Instructions:\n"
            "1. Remove any duplicate facts.\n"
            "2. Group similar points together (e.g., accessibility, rules, tips).\n"
            "3. Keep it brief and bulleted.\n"
            "4. DO NOT repeat the main description of the attraction. Focus ONLY on 'Additional Info'/metadata.\n"
            "5. If the information is missing or empty, simply say 'No specific additional info found.'\n"
            "6. Output in clean Markdown bullet points."
        )
        
        user_content = f"Attraction Query: {query}\n\nRaw Metadata gathered:\n{raw_info}"
        
        response = ollama.chat(
            model="qwen3:0.6b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response['message']['content']
        
    except Exception as e:
        return f"Error gathering info: {e}"

def OrchestrateAgent(query: str) -> str:
    """
    Orchestrator agent that combines TravelResearchAgent and AdditionalInfoAgent.
    """
    print(f"🤖 [OrchestrateAgent] Coordinating agents for query: {query}")
    
    # 1. Get specific additional details first (The Specialist)
    supplementary_info = AdditionalInfoAgent(query)
    
    # Check if we got real info or just a 'not found' message
    if not supplementary_info or "no specific additional information found" in supplementary_info.lower():
        supplementary_info = None

    # 2. Get the primary research/synthesis (The Engine) 
    # and feed the supplementary info into it
    final_response = TravelResearchAgent(query, additional_info=supplementary_info)
    
    return final_response

if __name__ == "__main__":
    # Simple test
    q = "tell me about madame tussauds"
    print(OrchestrateAgent(q))
