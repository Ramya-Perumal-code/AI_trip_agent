from tool_calls import search_rag
import json

query = "Admission to Madame Tussauds London"
print(f"Query: {query}")
results = search_rag(query, k=3)

print(f"Found {len(results)} results.")

for i, (doc, score) in enumerate(results):
    content = ""
    # Try metadata extraction logic from llm_agent.py to see exactly what the agent sees
    if hasattr(doc, 'metadata') and doc.metadata and 'data' in doc.metadata:
            data = doc.metadata['data']
            if isinstance(data, dict):
                content = data.get('markdown', str(data))
            elif isinstance(data, str):
                try:
                    data_json = json.loads(data)
                    content = data_json.get('markdown', str(data_json))
                except:
                    content = data
    
    if not content:
        content = getattr(doc, 'page_content', str(doc))

    with open('rag_dump.txt', 'a', encoding='utf-8') as f:
        f.write(f"\nResult {i+1} (Score: {score}):\n")
        f.write(f"--- Content Start ---\n{content}\n--- Content End ---\n")
        f.write("-" * 50 + "\n")
print("Dumped results to rag_dump.txt")
