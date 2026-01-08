import json
import re
import ollama
import importlib.util
import os

# Handle imports - works whether running from cookd_agent/ or parent directory
try:
    from tool_calls import search_rag, duckduckgo_search
except ImportError:
    from tool_calls import search_rag, duckduckgo_search


# --- Tool mapping for function calls ---
available_tools = {
    "search_rag": search_rag,
    "duckduckgo_search": duckduckgo_search,
}

import traceback

def extract_additional_info_section(text: str) -> str:
    """
    Extracts the 'Additional information' section.
    Simply looks for the header and captures EVERYTHING after it.
    """
    try:
        # Simplified regex: Find header, capture everything else.
        # (?i) = case insensitive
        # (?: ... ) = non-capturing header group
        # [:\s]+ = match colon and/or whitespace after header
        # (.*) = capture everything else (using DOTALL)
        pattern = r"(?i)(?:###\s*Additional information|additional Information)[:\s]+(.*)"
        
        match = re.search(pattern, text, re.DOTALL)
        if match:
             return match.group(1).strip()
        
        # Debugging: If no match, check if "Information" is even in the text
        if "Information" in text or "information" in text:
            # Find index of "Information" to show context
            idx = text.lower().find("information")
            start = max(0, idx - 50)
            end = min(len(text), idx + 100)
            print(f"DEBUG NO MATCH. Context around 'information': ...{text[start:end]}...")

    except Exception as e:
        print(f"⚠️ [Processing] Error parsing section: {e}")
        import traceback
        traceback.print_exc()
    
    return ""

# --- Final Response Agent ---
def FinalResponseAgent(content: str, user_query: str = "") -> str:
    """
    Generates a comprehensive final response based on gathered information.
    This agent synthesizes all collected data into a clear, user-friendly answer.
    If additional information is needed to answer the user's query, it can automatically use available tools.
    The agent will first check search_rag (local RAG) for information, and only use duckduckgo_search if RAG lacks info.
    
    Args:
        content: The gathered information/content to synthesize into a final response
        user_query: The original user query (optional, for context)
    
    Returns:
        str: A comprehensive final response to the user's query
    """
    # System prompt altered to instruct order of tool usage: search_rag first, then duckduckgo_search if needed.
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
        "5. Always try to fill in ALL key gaps, especially for reviews, ratings, restrictions, what is included/not included, and pricing/ticketing (make a follow-up duckduckgo_search if any are missing after search_rag).\n"
        "6. Once you have comprehensive information, synthesize everything into a clear, well-structured, user-friendly answer in MARKDOWN format.\n"
        "7. Do NOT include tool call syntax (like <search_rag> or <duckduckgo_search>) in your response.\n"
        "8. Do NOT include phrases like 'Final Answer', 'Final Response', 'Answer:', or similar labels - just provide the information directly.\n"
        "9. Organize content logically in sections with markdown headings/lists. Highlight important restrictions and included/not included items prominently.\n"
        "10. Begin directly with the information—no introductions or labels.\n"
        "11. VERIFY: Before responding, check that the attraction name in your response matches the user's query. If it doesn't match, do not provide that information."
    )

    print(f"🔍 [FinalResponseAgent] User query: {user_query}")
    print(f"🔍 [FinalResponseAgent] Initial content length: {len(content.strip()) if content else 0}")
    
    # --- RAG SEARCH ---
    # Always check RAG to ensure we have the most specific local data
    print(f"🔍 [FinalResponseAgent] Searching RAG for: '{user_query}'")
    try:
        rag_results = search_rag(query=user_query, k=5)
        
        if rag_results:
            print(f"✅ [FinalResponseAgent] RAG found {len(rag_results)} documents")
            rag_content_parts = []
            for doc, score in rag_results:
                # Extract content - Prioritize 'data' -> 'markdown' from metadata
                doc_text = ""
                
                # 1. Try metadata['data'] (Rich content)
                if hasattr(doc, 'metadata') and doc.metadata and 'data' in doc.metadata:
                    try:
                        data_content = doc.metadata['data']
                        # Handle double serialization if needed
                        if isinstance(data_content, str):
                            data_obj = json.loads(data_content)
                        else:
                            data_obj = data_content
                            
                        # Try to get markdown
                        if isinstance(data_obj, dict) and 'markdown' in data_obj:
                             doc_text = data_obj['markdown']
                             print(f"✅ [FinalResponseAgent] Using 'markdown' from metadata['data'] ({len(doc_text)} chars)")
                        elif isinstance(data_obj, dict):
                             # Fallback to dumping the whole data object if no markdown
                             doc_text = json.dumps(data_obj, default=str)
                        else:
                             doc_text = str(data_obj)
                    except Exception as e:
                        print(f"⚠️ [FinalResponseAgent] Error parsing metadata['data']: {e}")
                
                # 2. Fallback to page_content
                if not doc_text:
                    doc_text = getattr(doc, 'page_content', str(doc))

                rag_content_parts.append(f"Source (RAG, Score: {score}):\n{doc_text}\n---")
            
            rag_full_text = "\n".join(rag_content_parts)
            
            # Combine logic: Appending RAG results to existing content
            if content:
                content = content + "\n\n--- ADDITIONAL RAG INFO ---\n" + rag_full_text
            else:
                content = rag_full_text
        else:
             print(f"⚠️ [FinalResponseAgent] RAG returned no results")

    except Exception as e:
        print(f"❌ [FinalResponseAgent] RAG search error: {e}")

    # --- WEB SEARCH FALLBACK ---
    # If content is still sparse, try DuckDuckGo
    # (Threshold: < 100 chars seems reasonable for 'sparse')
    if not content or len(content.strip()) < 100:
        print(f"🔍 [FinalResponseAgent] Content sparse. Searching DuckDuckGo for: '{user_query}'")
        try:
            ddg_result = duckduckgo_search(query=user_query, max_results=3)
            if ddg_result and ddg_result.get("status") == "success":
                results = ddg_result.get("results", [])
                web_content_parts = []
                
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            title = item.get("title", "")
                            snippet = item.get("snippet", item.get("body", ""))
                            web_content_parts.append(f"Source (Web: {title}):\n{snippet}\n---")
                        else:
                            web_content_parts.append(str(item))
                elif isinstance(results, str):
                    web_content_parts.append(results)
                
                web_full_text = "\n".join(web_content_parts)
                 # Combine logic
                if content:
                    content = content + "\n\n--- ADDITIONAL WEB INFO ---\n" + web_full_text
                else:
                    content = web_full_text
                
                print(f"✅ [FinalResponseAgent] Web search added {len(web_full_text)} chars")
        except Exception as e:
             print(f"❌ [FinalResponseAgent] DuckDuckGo search error: {e}")


    # --- FINAL SYNTHESIS ---
    final_user_prompt = (
        f"User Query: {user_query}\n\n"
        f"Gathered Information:\n{content}\n\n"
        f"Instructions:\n"
        f"Synthesize a comprehensive answer based ONLY on the Gathered Information above. "
        f"Prefer RAG information if available. "
        f"If the information mentions conflicting attractions (e.g. 'San Diego Zoo' vs 'Legoland'), "
        f"ONLY use the information relevant to '{user_query}'."
    )

    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": final_user_prompt}
    ]

    try:
        response = ollama.chat(
            model="qwen3:0.6b",
            messages=conversation,
            tools=[],
        )
        msg = getattr(response, "message", None)
        final_response = msg.content.strip() if (msg and hasattr(msg, "content") and msg.content) else ""
        
        print(f"📝 [FinalResponseAgent] Final reponse generated ({len(final_response)} chars)")
        return final_response

    except Exception as e:
        print(f"❌ [FinalResponseAgent] LLM generation error: {e}")
        return "I apologize, but I encountered an error generating the final response."


# --- Additional Info Agent ---
def AdditionalInfoAgent(query: str) -> str:
    """
    Agent that gathers additional information using RAG and web search tools.
    Uses both local knowledge base (RAG) and DuckDuckGo web search to find relevant information.
    The LLM decides which tools to call (search_rag, duckduckgo_search).
    
    Args:
        query: The query to gather information about (e.g., "Las Vegas attractions", "San Diego Zoo guide")
    
    Returns:
        str: Comprehensive information gathered from RAG and web search
    """
    print(f"\n🔍 [AdditionalInfoAgent] Gathering information for: {query}")
    
    rag_context = "" # Initialize RAG context

    # 1. ALWAYS Try RAG First explicitly
    try:
        print(f"🔍 [AdditionalInfoAgent] Checking RAG first for: '{query}'")
        rag_results = search_rag(query=query, k=3)
        print(rag_results)
        if rag_results:
             print(f"✅ [AdditionalInfoAgent] RAG found {len(rag_results)} documents")
             formatted_rag = []
             found_section = False
             
             for doc, score in rag_results:
                 # Try to extract from Metadata JSON first (Most Reliable)
                 extracted_from_json = False
                 if hasattr(doc, 'metadata') and doc.metadata and 'json' in doc.metadata:
                     print(f"DEBUG: doc.metadata keys: {list(doc.metadata.keys())}") # Debug keys
                     try:
                         json_str = doc.metadata['json']
                         # Handle case where it might be double-serialized or just a dict
                         if isinstance(json_str, str):
                             data = json.loads(json_str)
                         else:
                             data = json_str
                         
                         # Check for specific keys
                         possible_keys = ["additional Information", "Additional information", "Additional Information", "additional information"]
                         
                         # Determine the correct dictionary to search in
                         # Case 1: Nested structure like {"success": true, "data": {"json": {...}}} 
                         # (Logic matching user's finding)
                         target_data = {}
                         if isinstance(data, dict):
                             if 'data' in data and isinstance(data['data'], dict) and 'json' in data['data']:
                                 target_data = data['data']['json']
                             # Case 2: Potentially flat structure or different nesting
                             elif 'json' in data and isinstance(data['json'], dict):
                                 target_data = data['json']
                             else:
                                 target_data = data
                         
                         for key in possible_keys:
                             if key in target_data and target_data[key]:
                                 info_content = target_data[key]
                                 # Format if it's a list
                                 if isinstance(info_content, list):
                                     info_text = "\n".join([str(i) for i in info_content])
                                 else:
                                     info_text = str(info_content)
                                     
                                 print(f"✅ [AdditionalInfoAgent] Found '{key}' in metadata JSON.")
                                 formatted_rag.append(f"Source (RAG Metadata '{key}', Score: {score}):\n{info_text}\n---")
                                 found_section = True
                                 extracted_from_json = True
                                 break
                     except Exception as e:
                         print(f"⚠️ [AdditionalInfoAgent] Error parsing metadata JSON: {e}")
                         import traceback
                         traceback.print_exc()

                 # If not found in JSON, try Regex on page_content (Fallback)
                 if not extracted_from_json:
                     doc_text = getattr(doc, 'page_content', str(doc))
                     section_content = extract_additional_info_section(doc_text)
                     
                     if section_content:
                         print(f"✅ [AdditionalInfoAgent] Found section via Regex: {section_content[:50]}...")
                         formatted_rag.append(f"Source (RAG Regex 'Additional Info', Score: {score}):\n{section_content}\n---")
                         found_section = True
                     else:
                         print(f"⚠️ [AdditionalInfoAgent] 'Additional information' section not found in doc (Metadata or Regex).")
             
             if formatted_rag:
                 rag_context = "\n".join(formatted_rag)
                 rag_context = f"EXISTING KNOWLEDGE (RAG - Additional Information Only):\n{rag_context}\n\n"
             elif not found_section:
                 print(f"⚠️ [AdditionalInfoAgent] No 'Additional information' sections found in any RAG docs.")
                 # Fallback: maybe the docs ARE the info? 
                 # But sticking to user request: "get only..."
        else:
             print(f"⚠️ [AdditionalInfoAgent] RAG returned no results")
    except Exception as e:
        print(f"❌ [AdditionalInfoAgent] RAG search error: {e}")
        traceback.print_exc()
    
    system_prompt = (
        "You are an Additional Info Agent specialized in gathering comprehensive information about travel, "
        "attractions, and trip planning.\n\n"
        "You have access to tools:\n"
        "- search_rag: Search the local knowledge base (Use this if existing knowledge is insufficient)\n"
        "- duckduckgo_search: Search the web for additional current information\n\n"
        "Instructions:\n"
        "1. Analyze the 'EXISTING KNOWLEDGE' provided (if any).\n"
        "2. If the existing knowledge answers the query comprehensively, you can return the answer directly.\n"
        "3. If information is missing (e.g., ticket prices, missing details), call `duckduckgo_search` or `search_rag` (if you think more local info exists).\n"
        "4. Synthesize ALL information (Existing + New) into a comprehensive MARKDOWN response."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        # Inject RAG context into the user message
        {"role": "user", "content": f"{rag_context}Gather comprehensive information about: {query}"}
    ]
    
    # Tool list for Ollama
    tools_list = [search_rag, duckduckgo_search]
    
    while True:
        response = ollama.chat(
            model="qwen3:0.6b",
            messages=messages,
            tools=tools_list,
        )
        
        msg = response.message
        
        # Handle tool calls
        if msg.tool_calls:
            all_results = []
            for tool in msg.tool_calls:
                fn_name = tool.function.name
                fn_args = tool.function.arguments
                
                # Handle arguments - might be dict or JSON string
                if isinstance(fn_args, str):
                    fn_args = json.loads(fn_args)
                elif isinstance(fn_args, dict):
                    fn_args = fn_args
                else:
                    fn_args = {}
                
                print(f"\n🔧 [AdditionalInfoAgent] Calling tool: {fn_name} with {fn_args}")
                
                if fn_name in available_tools:
                    try:
                        result = available_tools[fn_name](**fn_args)
                        print(f"📦 [AdditionalInfoAgent] {fn_name} returned results")
                        
                        # Format result for message
                        if isinstance(result, dict):
                            result_str = json.dumps(result, indent=2)
                        elif isinstance(result, list):
                            # Handle list of tuples (doc, score) from search_rag
                            if len(result) > 0 and isinstance(result[0], tuple):
                                formatted_results = []
                                for doc, score in result:
                                    formatted_results.append({
                                        "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                                        "score": float(score) if score else 0.0,
                                        "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                                    })
                                result_str = json.dumps(formatted_results, indent=2)
                            else:
                                result_str = json.dumps(result, indent=2, default=str)
                        else:
                            result_str = str(result)
                        
                        all_results.append(result_str)
                        
                        # Add tool call and result to messages
                        messages.append({
                            "role": "assistant",
                            "content": msg.content or "",
                            "tool_calls": [{"function": {"name": fn_name, "arguments": fn_args}}]
                        })
                        messages.append({
                            "role": "tool",
                            "content": result_str
                        })
                    except Exception as e:
                        error_msg = f"Error calling {fn_name}: {str(e)}"
                        print(f"❌ [AdditionalInfoAgent] {error_msg}")
                        messages.append({
                            "role": "assistant",
                            "content": msg.content or "",
                            "tool_calls": [{"function": {"name": fn_name, "arguments": fn_args}}]
                        })
                        messages.append({
                            "role": "tool",
                            "content": error_msg
                        })
                else:
                    error_msg = f"Unknown tool: {fn_name}"
                    print(f"❌ [AdditionalInfoAgent] {error_msg}")
                    messages.append({
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [{"function": {"name": fn_name, "arguments": fn_args}}]
                    })
                    messages.append({
                        "role": "tool",
                        "content": error_msg
                    })
            
            # Add a reminder message to synthesize the results into markdown
            messages.append({
                "role": "user",
                "content": "Now synthesize all the information from the tool results into a comprehensive markdown-formatted response. Use headings, lists, and paragraphs. Do NOT include any tool call syntax in your response."
            })
            
            # Continue loop to get final response after tool calls
            continue
        
        # If no tool calls, return the final response
        if msg.content:
            gathered_info = msg.content.strip()
            
            # Clean up any tool call syntax that might have been included in the response
            # Remove tool call tags like <search_rag>...</search_rag> or <duckduckgo_search>...</duckduckgo_search>
            gathered_info = re.sub(r'<search_rag>.*?</search_rag>', '', gathered_info, flags=re.DOTALL)
            gathered_info = re.sub(r'<duckduckgo_search>.*?</duckduckgo_search>', '', gathered_info, flags=re.DOTALL)
            # Remove standalone tool call tags
            gathered_info = re.sub(r'</?(search_rag|duckduckgo_search)[^>]*>', '', gathered_info)
            # Clean up extra whitespace
            gathered_info = re.sub(r'\n\s*\n\s*\n', '\n\n', gathered_info)
            gathered_info = gathered_info.strip()
            
            print(f"✅ [AdditionalInfoAgent] Information gathered: {gathered_info[:150]}...")
            return gathered_info
        
        # Fallback if no content
        return "Unable to gather additional information."


# Example usage:
if __name__ == "__main__":
    test_query = "Admission to Madame Tussauds London?"
    
    print("=" * 50)
    print("Testing AdditionalInfoAgent -> FinalResponseAgent Chain")
    print("=" * 50)
    
    # 1. Gather Info (RAG First)
    gathered_info = AdditionalInfoAgent(test_query)
    # print(f"\n[Main] Gathered Info (Preview): {gathered_info if gathered_info else 'None'}...\n")
    
    # 2. Generate Final Response
    final_response = FinalResponseAgent(gathered_info, test_query)
    print(f"\nFinal Response:\n{final_response}\n")
