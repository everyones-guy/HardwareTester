import requests
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.extensions import db

# Initialize logger
logger = CustomLogger.get_logger("api_service")

logger.info("Initializing APIService")


class APIService:
    api_state = {
        "initialized": False,
        "running": False,
        "config": {
            "default_machine_name": "Session1",
            "stress_test_mode": False,
            "base_url": None,
            "timeout": 10,
        },
        "blueprints": [],
        "active_sessions": [],
        "endpoints": [],
        "logs": [],
        "errors": [],
        "last_updated": None,
    }

    @staticmethod
    def _get_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
        """
        Configures a session with retry logic for resilient requests.
        """
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

    session = _get_session_with_retries()

    @staticmethod
    def initialize(base_url: str, timeout: int = 10):
        """
        Initialize the APIService with a base URL and timeout.
        """
        if not base_url:
            raise ValueError("Base URL must be provided for initialization.")
        
        APIService.api_state["config"]["base_url"] = base_url
        APIService.api_state["config"]["timeout"] = timeout
        APIService.api_state["initialized"] = True
        APIService.api_state["last_updated"] = datetime.now()
        APIService.api_state["logs"].append(f"APIService initialized at {APIService.api_state['last_updated']}")
        logger.info(f"APIService initialized with base URL: {base_url} and timeout: {timeout}")

    @staticmethod
    def log_error(error_message):
        """
        Log an error in the API state and persist it in logs.
        """
        error_entry = {
            "timestamp": datetime.now(),
            "message": error_message,
        }
        APIService.api_state["errors"].append(error_entry)
        APIService.api_state["last_updated"] = datetime.now()
        logger.error(f"Error logged: {error_message}")

    @staticmethod
    def test_api_connection():
        """
        Test the connection to the API.
        """
        try:
            base_url = APIService.api_state["config"]["base_url"]
            if not base_url:
                raise RuntimeError("APIService is not initialized with a base URL.")

            timeout = APIService.api_state["config"]["timeout"]
            response = APIService.session.get(f"{base_url}/test-connection", timeout=timeout)
            response.raise_for_status()
            logger.info("API connection successful.")
            return {"success": True, "message": "API connection successful"}
        except requests.exceptions.RequestException as e:
            APIService.log_error(f"API connection failed: {e}")
            return {"success": False, "error": f"API connection failed: {e}"}

    @staticmethod
    def fetch_data_from_api(endpoint: str, params: dict = None) -> dict:
        """
        Fetch data from a specified API endpoint.
        """
        try:
            base_url = APIService.api_state["config"]["base_url"]
            if not base_url:
                raise RuntimeError("APIService is not initialized with a base URL.")

            timeout = APIService.api_state["config"]["timeout"]
            response = APIService.session.get(f"{base_url}{endpoint}", params=params, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Data fetched successfully from {endpoint}.")
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            APIService.log_error(f"Failed to fetch data from {endpoint}: {e}")
            return {"success": False, "error": f"Failed to fetch data from {endpoint}: {e}"}

    @staticmethod
    def push_data_to_api(endpoint: str, payload: dict) -> dict:
        """
        Push data to a specified API endpoint.
        """
        try:
            base_url = APIService.api_state["config"]["base_url"]
            if not base_url:
                raise RuntimeError("APIService is not initialized with a base URL.")

            timeout = APIService.api_state["config"]["timeout"]
            response = APIService.session.post(f"{base_url}{endpoint}", json=payload, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Data pushed successfully to {endpoint}.")
            return {"success": True, "message": "Data successfully pushed"}
        except requests.exceptions.RequestException as e:
            APIService.log_error(f"Failed to push data to {endpoint}: {e}")
            return {"success": False, "error": f"Failed to push data to {endpoint}: {e}"}

    @staticmethod
    def list_available_endpoints() -> dict:
        """
        Fetch the list of available API endpoints.
        """
        try:
            base_url = APIService.api_state["config"]["base_url"]
            if not base_url:
                raise RuntimeError("APIService is not initialized with a base URL.")

            timeout = APIService.api_state["config"]["timeout"]
            response = APIService.session.get(f"{base_url}/endpoints", timeout=timeout)
            response.raise_for_status()
            endpoints = response.json().get("endpoints", [])
            APIService.api_state["endpoints"] = endpoints
            APIService.api_state["last_updated"] = datetime.now()
            logger.info(f"Discovered {len(endpoints)} endpoints.")
            return {"success": True, "endpoints": endpoints}
        except requests.exceptions.RequestException as e:
            APIService.log_error(f"Failed to fetch endpoints: {e}")
            return {"success": False, "error": f"Failed to fetch endpoints: {e}"}

    @staticmethod
    def get_overview() -> dict:
        """
        Fetch a summarized API overview.
        """
        try:
            base_url = APIService.api_state["config"]["base_url"]
            if not base_url:
                raise RuntimeError("APIService is not initialized with a base URL.")

            timeout = APIService.api_state["config"]["timeout"]
            response = APIService.session.get(f"{base_url}/overview", timeout=timeout)
            response.raise_for_status()
            overview_data = response.json()
            logger.info("Successfully fetched API overview.")
            return {"success": True, "overview": overview_data}
        except requests.exceptions.RequestException as e:
            APIService.log_error(f"Failed to fetch API overview: {e}")
            return {"success": False, "error": f"Failed to fetch API overview: {e}"}
