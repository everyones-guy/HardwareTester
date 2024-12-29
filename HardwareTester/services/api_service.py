
import requests
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Initialize logger
logger = logging.getLogger("APIService")

# Configure session with retry strategy
def _get_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Create a session object
session = _get_session_with_retries()

def test_api_connection():
    """Test API connection."""
    try:
        base_url = current_app.config["BASE_URL"]
        timeout = current_app.config.get("API_TIMEOUT", 5)
        response = session.get(f"{base_url}/test-connection", timeout=timeout)
        response.raise_for_status()
        logger.info("API connection successful.")
        return {"success": True, "message": "API connection successful"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to API: {e}")
        return {"success": False, "error": f"API connection failed: {e}"}

def fetch_data_from_api(endpoint, params=None):
    """Fetch data from an API endpoint."""
    try:
        base_url = current_app.config["BASE_URL"]
        timeout = current_app.config.get("API_TIMEOUT", 10)
        response = session.get(f"{base_url}{endpoint}", params=params, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Fetched data from {endpoint}.")
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from {endpoint}: {e}")
        return {"success": False, "error": f"Failed to fetch data: {e}"}

def push_data_to_api(endpoint, payload):
    """Push data to an API endpoint."""
    try:
        base_url = current_app.config["BASE_URL"]
        timeout = current_app.config.get("API_TIMEOUT", 10)
        response = session.post(f"{base_url}{endpoint}", json=payload, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Data pushed to {endpoint} successfully.")
        return {"success": True, "message": "Data successfully pushed"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to push data to {endpoint}: {e}")
        return {"success": False, "error": f"Failed to push data: {e}"}

def list_available_endpoints():
    """Return a list of API endpoints."""
    try:
        base_url = current_app.config["BASE_URL"]
        timeout = current_app.config.get("API_TIMEOUT", 10)
        response = session.get(f"{base_url}/endpoints", timeout=timeout)
        response.raise_for_status()
        endpoints = response.json().get("endpoints", [])
        logger.info(f"Discovered {len(endpoints)} endpoints.")
        return {"success": True, "endpoints": endpoints}
    except requests.exceptions.RequestException:
        logger.warning("Failed to fetch endpoints from API. Using static list.")
        # Fallback to static list
        endpoints = ["/example-endpoint", "/another-endpoint", "/test-connection"]
        return {"success": True, "endpoints": endpoints}
    except Exception as e:
        logger.error(f"Unexpected error while listing endpoints: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}

