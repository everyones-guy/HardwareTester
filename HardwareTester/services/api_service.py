import requests

BASE_URL = "https://example.com/api"  # Replace with your API's base URL

def test_api_connection():
    """Test API connection."""
    try:
        response = requests.get(f"{BASE_URL}/test-connection", timeout=5)
        response.raise_for_status()
        return {"success": True, "message": "API connection successful"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def fetch_data_from_api(endpoint, params):
    """Fetch data from an API endpoint."""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def push_data_to_api(endpoint, payload):
    """Push data to an API endpoint."""
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=10)
        response.raise_for_status()
        return {"success": True, "message": "Data successfully pushed"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def list_available_endpoints():
    """Return a list of mock API endpoints (or fetch dynamically if possible)."""
    try:
        # Example static list for now
        endpoints = ["/example-endpoint", "/another-endpoint", "/test-connection"]
        return {"success": True, "endpoints": endpoints}
    except Exception as e:
        return {"success": False, "error": str(e)}
