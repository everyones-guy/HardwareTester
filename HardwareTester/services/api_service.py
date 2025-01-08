import requests
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from HardwareTester.extensions import db, logger
from HardwareTester.models.device_models import Device, Peripheral, Controller, Emulation

# Configure session with retry strategy
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
        APIService.api_state["config"]["base_url"] = base_url
        APIService.api_state["config"]["timeout"] = timeout
        APIService.api_state["initialized"] = True
        APIService.api_state["last_updated"] = datetime.now()
        APIService.api_state["logs"].append(f"APIService initialized at {APIService.api_state['last_updated']}")
        logger.info("APIService initialized successfully.")

    @staticmethod
    def update_state(key, value):
        if key in APIService.api_state:
            APIService.api_state[key] = value
            APIService.api_state["last_updated"] = datetime.now()
            logger.info(f"API state updated: {key} -> {value}")

    @staticmethod
    def add_blueprint(blueprint_name, description):
        blueprint = {
            "name": blueprint_name,
            "description": description,
            "created_at": datetime.now(),
        }
        APIService.api_state["blueprints"].append(blueprint)
        APIService.api_state["last_updated"] = datetime.now()
        logger.info(f"Added blueprint: {blueprint}")

    @staticmethod
    def log_error(error_message):
        error_entry = {
            "timestamp": datetime.now(),
            "message": error_message,
        }
        APIService.api_state["errors"].append(error_entry)
        APIService.api_state["last_updated"] = datetime.now()
        logger.error(f"Error logged: {error_message}")

    @staticmethod
    def test_api_connection():
        try:
            base_url = current_app.config["BASE_URL"]
            timeout = current_app.config.get("API_TIMEOUT", 5)
            response = APIService.session.get(f"{base_url}/test-connection", timeout=timeout)
            response.raise_for_status()
            logger.info("API connection successful.")
            return {"success": True, "message": "API connection successful"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to API: {e}")
            return {"success": False, "error": f"API connection failed: {e}"}

    @staticmethod
    def fetch_data_from_api(endpoint: str, params: dict = None) -> dict:
        try:
            base_url = current_app.config["BASE_URL"]
            timeout = current_app.config.get("API_TIMEOUT", 10)
            response = APIService.session.get(f"{base_url}{endpoint}", params=params, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Fetched data successfully from {endpoint}.")
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from {endpoint}: {e}")
            return {"success": False, "error": f"Failed to fetch data from {endpoint}: {e}"}

    @staticmethod
    def push_data_to_api(endpoint, payload):
        try:
            base_url = current_app.config["BASE_URL"]
            timeout = current_app.config.get("API_TIMEOUT", 10)
            response = APIService.session.post(f"{base_url}{endpoint}", json=payload, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Data pushed to {endpoint} successfully.")
            return {"success": True, "message": "Data successfully pushed"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to push data to {endpoint}: {e}")
            return {"success": False, "error": f"Failed to push data: {e}"}

    @staticmethod
    def list_available_endpoints():
        try:
            base_url = current_app.config["BASE_URL"]
            timeout = current_app.config.get("API_TIMEOUT", 10)
            response = APIService.session.get(f"{base_url}/endpoints", timeout=timeout)
            response.raise_for_status()
            endpoints = response.json().get("endpoints", [])
            logger.info(f"Discovered {len(endpoints)} endpoints.")
            return {"success": True, "endpoints": endpoints}
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to fetch endpoints from API. Using static list.")
            return {"success": True, "endpoints": ["/example-endpoint", "/another-endpoint", "/test-connection"]}
        except Exception as e:
            logger.error(f"Unexpected error while listing endpoints: {e}")
            return {"success": False, "error": f"Unexpected error: {e}"}

    @staticmethod
    def get_overview():
        """
        Fetch an overview of the API state or system status.
        :return: Dictionary containing overview details or an error message.
        """
        try:
            base_url = current_app.config["BASE_URL"]
            timeout = current_app.config.get("API_TIMEOUT", 10)
            response = APIService.session.get(f"{base_url}/overview", timeout=timeout)
            response.raise_for_status()
            overview_data = response.json()
            logger.info("Successfully fetched API overview.")
            return {"success": True, "overview": overview_data}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch API overview: {e}")
            return {"success": False, "error": f"Failed to fetch API overview: {e}"}
