import requests
import json
import os

# Base URL for the GetYourGuide Partner API (Mock/Placeholder)
# Real endpoint would be something like: https://api.getyourguide.com/1
BASE_URL = "https://api.getyourguide.com/1"
API_KEY = os.getenv("GYG_API_KEY", "your_api_key_here")

def get_headers():
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

def search_tours(query, limit=5):
    """
    Searches for tours/activities. 
    In a real scenario, this would hit the /tours endpoint.
    """
    print(f"Searching for: {query}")
    
    # MOCK RESPONSE
    # Simulating what the API might return for a query like "Venice"
    mock_results = [
        {
            "tour_id": "12345",
            "title": "Venice: Grand Canal Gondola Ride",
            "rating": 4.8,
            "reviews": 1200,
            "price": {"amount": 35.00, "currency": "EUR"},
            "duration": "30 minutes"
        },
        {
            "tour_id": "67890",
            "title": "Venice: Doge's Palace Skip-the-Line Tour",
            "rating": 4.7,
            "reviews": 850,
            "price": {"amount": 45.00, "currency": "EUR"},
            "duration": "1 hour"
        }
    ]
    
    return mock_results

def get_tour_details(tour_id):
    """
    Fetches detailed information for a specific tour.
    Maps the GYG response to the project's required JSON structure.
    """
    print(f"Fetching details for tour ID: {tour_id}")
    
    # MOCK RESPONSE for Tour ID 12345
    if tour_id == "12345":
        gyg_raw_data = {
            "id": "12345",
            "name": "Venice: Grand Canal Gondola Ride",
            "description": "Experience the magic of restricted waterways...",
            "highlights": ["Glide down the Grand Canal", "See historic palazzos"],
            "inclusions": ["Gondola ride", "Live commentary"],
            "exclusions": ["Food and drink", "Hotel pickup"],
            "meeting_point": "St. Mark's Square, by the column",
            "requirements": ["No large bags"],
            "coordinates": {"lat": 45.434, "lon": 12.339},
            "rating": 4.8,
            "duration_min": 30,
            "know_before_you_go": ["Ride is shared with others", "Weather dependent"]
        }
    else:
        # Default mock
        gyg_raw_data = {
            "id": tour_id,
            "name": "Sample Tour",
            "description": "A sample tour description.",
            "highlights": ["Highlight 1", "Highlight 2"],
            "inclusions": ["Inclusion 1"],
            "exclusions": ["Exclusion 1"],
            "requirements": ["Requirement 1"],
            "rating": 4.5,
            "duration_min": 60,
             "know_before_you_go": ["Info 1"]
        }

    # MAPPING to project structure
    formatted_data = {
        "Attraction_name": gyg_raw_data.get("name"),
        "Why visit": gyg_raw_data.get("highlights", []),
        "What included": gyg_raw_data.get("inclusions", []),
        "What not included": gyg_raw_data.get("exclusions", []), # Added for completeness matching schema
        "Restrictions": gyg_raw_data.get("requirements", []),
        "Location": [f"Meeting Point: {gyg_raw_data.get('meeting_point', 'See ticket')} "],
        "User Rating": f"{gyg_raw_data.get('rating')} stars",
        "Duration": f"{gyg_raw_data.get('duration_min')} minutes",
        "additional Information": gyg_raw_data.get("know_before_you_go", [])
    }
    
    return formatted_data

def save_to_dataset(data, filename="gyg_output.json"):
    """
    Saves the formatted data to a JSON file in the dataset_json folder.
    """
    output_dir = "dataset_json"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    full_structure = {
        "success": True,
        "data": {
            "markdown": f"# {data['Attraction_name']}\n\n{data['Attraction_name']}...", # Minimal markdown for now
            "metadata": {
                "source": "GetYourGuide API",
                "id": "mock_id"
            },
            "json": data
        }
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(full_structure, f, indent=2)
    print(f"Saved to {filepath}")

# Example Usage
if __name__ == "__main__":
    # 1. Search for tours
    results = search_tours("Venice")
    
    if results:
        # 2. Get details for the first result
        first_tour_id = results[0]["tour_id"]
        tour_details = get_tour_details(first_tour_id)
        
        # 3. Print result
        print(json.dumps(tour_details, indent=2))
        
        # 4. Save to file (mimicking the scraper output)
        save_to_dataset(tour_details, "gyg_venice_gondola.json")
