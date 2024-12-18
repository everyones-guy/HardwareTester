from flask import current_app
import requests

def test_api_connection():
    """Test API connection."""
    try:
        base_url = current_app.config["BASE_URL"]
        response = requests.get(f"{base_url}/test-connection", timeout=5)
        response.raise_for_status()
        return {"success": True, "message": "API connection successful"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def fetch_data_from_api(endpoint, params):
    """Fetch data from an API endpoint."""
    try:
        base_url = current_app.config["BASE_URL"]
        response = requests.get(f"{base_url}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def push_data_to_api(endpoint, payload):
    """Push data to an API endpoint."""
    try:
        base_url = current_app.config["BASE_URL"]
        response = requests.post(f"{base_url}{endpoint}", json=payload, timeout=10)
        response.raise_for_status()
        return {"success": True, "message": "Data successfully pushed"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def list_available_endpoints():
    """Return a list of mock API endpoints."""
    try:
        # Example static list for now
        endpoints = ["/example-endpoint", "/another-endpoint", "/test-connection"]
        return {"success": True, "endpoints": endpoints}
    except Exception as e:
        return {"success": False, "error": str(e)}
