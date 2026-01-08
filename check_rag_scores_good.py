from tool_calls import search_rag

query = "Booking.com"
print(f"Query: {query}")
results = search_rag(query, k=3)

for doc, score in results:
    print(f"Score: {score}")
    print(f"Content Preview: {doc.page_content[:100]}...")
    print("---")
