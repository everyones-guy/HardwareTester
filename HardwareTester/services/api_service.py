
import requests
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from datetime import datetime


# Initialize logger
logger = logging.getLogger("APIService")

# Configure session with retry strategy - will likely be replaced by a state method like in the emulator service which will look like: 
 # Emulator state

class APIService:
    # Centralized state for API operations
    api_state = {
        "initialized": False,  # Tracks whether the service has been properly initialized
        "running": False,  # Indicates whether the API service is actively running
        "config": {
            "default_machine_name": "Session1",
            "stress_test_mode": False,
            "base_url": None,  # Base URL for the API, set during initialization
            "timeout": 10,  # Default timeout for API requests (in seconds)
        },
        "blueprints": [],  # Stores blueprint information (e.g., loaded blueprints for emulation)
        "active_sessions": [],  # Tracks active API sessions
        "endpoints": [],  # List of available API endpoints
        "logs": [],  # Holds log entries for debugging or tracking
        "errors": [],  # Tracks errors encountered during API calls
        "last_updated": None,  # Timestamp for the last state update
    }

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

    @staticmethod
    def initialize(base_url: str, timeout: int = 10):
        """
        Initialize the API state with necessary configuration.
        
        :param base_url: The base URL of the API.
        :param timeout: Default timeout for API requests.
        """
        APIService.api_state["config"]["base_url"] = base_url
        APIService.api_state["config"]["timeout"] = timeout
        APIService.api_state["initialized"] = True
        APIService.api_state["last_updated"] = datetime.now()
        APIService.api_state["logs"].append(f"APIService initialized at {APIService.api_state['last_updated']}")
        logging.info("APIService initialized successfully.")
        
    @staticmethod
    def update_state(key, value):
        """
        Update a specific key in the API state.
        
        :param key: The key to update.
        :param value: The new value for the key.
        """
        if key in APIService.api_state:
            APIService.api_state[key] = value
            APIService.api_state["last_updated"] = datetime.now()
            logging.info(f"API state updated: {key} -> {value}")
    
    @staticmethod
    def add_blueprint(blueprint_name, description):
        """
        Add a blueprint to the state.

        :param blueprint_name: Name of the blueprint.
        :param description: Description of the blueprint.
        """
        blueprint = {
            "name": blueprint_name,
            "description": description,
            "created_at": datetime.now(),
        }
        APIService.api_state["blueprints"].append(blueprint)
        APIService.api_state["last_updated"] = datetime.now()
        logging.info(f"Added blueprint: {blueprint}")
        
    @staticmethod
    def log_error(error_message):
        """
        Log an error to the API state.

        :param error_message: Description of the error.
        """
        error_entry = {
            "timestamp": datetime.now(),
            "message": error_message,
        }
        APIService.api_state["errors"].append(error_entry)
        APIService.api_state["last_updated"] = datetime.now()
        logging.error(f"Error logged: {error_message}")

    @staticmethod
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
    
    @staticmethod
    def fetch_data_from_api(endpoint: str, params: dict = None) -> dict:
        """Fetch data from an API endpoint."""
        try:
            base_url, timeout = APIService._get_base_url_and_timeout()
            response = session.get(f"{base_url}{endpoint}", params=params, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Fetched data successfully from {endpoint}.")
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from {endpoint}: {e}")
            return {"success": False, "error": f"Failed to fetch data from {endpoint}: {e}"}

    @staticmethod
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

    @staticmethod
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

