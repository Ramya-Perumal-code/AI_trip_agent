# API Key and Code Snippets
# API Key and Code Snippets
# Manage your API key and view code snippets.
# API Key
# fc-e****598a
# For complete documentation, SDKs and integrations, visit our documentation
# Scrape a web page
# Used to scrape a single URL. Returns markdown with the content of the URL.
# automate.py - Utility to fetch attraction data via Firecrawl API
"""
This script provides a reusable function to scrape a given URL using the Firecrawl API.
It reads the API key from the environment variable ``FIRECRAWL_API_KEY`` for security.
You can also run the script directly from the command line:

    python automate.py <url>

The function returns the JSON response from the API.
"""

import os
import sys
import argparse
import requests
from typing import Any, Dict
import json

# Base endpoint for Firecrawl scrape API
API_ENDPOINT = "https://api.firecrawl.dev/v2/scrape"

def fetch_attraction_data(url: str) -> Dict[str, Any]:
    """Fetch attraction data from Firecrawl.

    Args:
        url: The target webpage URL to scrape.

    Returns:
        The JSON response from the Firecrawl API as a Python dictionary.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "FIRECRAWL_API_KEY environment variable not set. Set it to your Firecrawl API key before running."
        )

    payload = {
        "url": url,
        "onlyMainContent": False,
        "maxAge": 172800000,
        "parsers": ["pdf"],
        "formats": [
            "markdown",
            {
                "type": "json",
                "schema": {
                    "type": "object",
                    "required": [],
                    "properties": {
                        "Attraction_name": {"type": "string"},
                        "Why visit": {"type": "array", "items": {"type": "string"}},
                        "What included": {"type": "array", "items": {"type": "string"}},
                        "What not included": {"type": "array", "items": {"type": "string"}},
                        "Restrictions": {"type": "array", "items": {"type": "string"}},
                        "Location": {"type": "array", "items": {"type": "string"}},
                        "User Rating": {"type": "string"},
                        "Duration": {"type": "string"},
                        "additional Information": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_ENDPOINT, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Fetch attraction data via Firecrawl.")
    parser.add_argument("url", help="The URL of the attraction page to scrape.")
    parser.add_argument("--output", help="Path to write JSON output file (optional)")
    args = parser.parse_args()
    try:
        data = fetch_attraction_data(args.url)
        print(data)
        print(args.output)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Response written to {args.output}")
        else:
            print(data)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()