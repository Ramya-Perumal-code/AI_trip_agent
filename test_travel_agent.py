from llm_agent import TravelResearchAgent
import sys

# Test query
query = "San Diego Zoo Ticket Prices"
if len(sys.argv) > 1:
    query = sys.argv[1]

print(f"Testing TravelResearchAgent with query: {query}")
try:
    response = TravelResearchAgent(query)
    print("\n--- Final Response ---\n")
    print(response)
    print("\n----------------------\n")
except Exception as e:
    print(f"Error running agent: {e}")
    import traceback
    traceback.print_exc()
