import os
import socket
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.services.hardware_service import HardwareService


# Load up the env file
load_dotenv()

# Fetch MQTT broker from .env with a fallback to "localhost"
MQTT_BROKER = os.getenv("MQTT_BROKER", socket.gethostbyname(socket.gethostname()))

# Initialize logger
logger = CustomLogger.get_logger("api_manager")

class APIManager:
    """Library for managing API connections and requests."""
    def __init__(self, base_url, mqtt_broker=MQTT_BROKER, default_timeout=30):
        """
        Initialize the API Manager.
        :param base_url: Base URL of the API.
        :param default_timeout: Default timeout for requests in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout
        self.mqtt_service = MQTTService(broker=mqtt_broker)  # Pass the broker from .env
        logger.info(f"APIManager initialized with base URL: {self.base_url}, MQTT Broker: {mqtt_broker}")

    def _log_request(self, method, url, payload=None, headers=None):
        """Log request details."""
        logger.debug(f"Request Method: {method}")
        logger.debug(f"URL: {url}")
        if payload:
            logger.debug(f"Payload: {payload}")
        if headers:
            logger.debug(f"Headers: {headers}")

    def _log_response(self, response):
        """Log response details."""
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Body: {response.text}")

    def get(self, endpoint, params=None, headers=None):
        """
        Make a GET request.
        :param endpoint: API endpoint to hit.
        :param params: Query parameters for the request.
        :param headers: Additional headers for the request.
        :return: Response JSON or error.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request("GET", url, payload=params, headers=headers)

        try:
            response = requests.get(url, params=params, headers=headers, timeout=self.default_timeout)
            self._log_response(response)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"GET request failed: {e}")
            return {"success": False, "error": str(e)}

    def post(self, endpoint, payload=None, headers=None):
        """
        Make a POST request.
        :param endpoint: API endpoint to hit.
        :param payload: Data to send in the body of the request.
        :param headers: Additional headers for the request.
        :return: Response JSON or error.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request("POST", url, payload=payload, headers=headers)

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.default_timeout)
            self._log_response(response)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"POST request failed: {e}")
            return {"success": False, "error": str(e)}

    def put(self, endpoint, payload=None, headers=None):
        """
        Make a PUT request.
        :param endpoint: API endpoint to hit.
        :param payload: Data to send in the body of the request.
        :param headers: Additional headers for the request.
        :return: Response JSON or error.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request("PUT", url, payload=payload, headers=headers)

        try:
            response = requests.put(url, json=payload, headers=headers, timeout=self.default_timeout)
            self._log_response(response)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"PUT request failed: {e}")
            return {"success": False, "error": str(e)}

    def delete(self, endpoint, headers=None):
        """
        Make a DELETE request.
        :param endpoint: API endpoint to hit.
        :param headers: Additional headers for the request.
        :return: Response JSON or error.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request("DELETE", url, headers=headers)

        try:
            response = requests.delete(url, headers=headers, timeout=self.default_timeout)
            self._log_response(response)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"DELETE request failed: {e}")
            return {"success": False, "error": str(e)}

    def test_connection(self):
        """
        Test the API connection by making a simple GET request to the base URL.
        :return: Connection status.
        """
        try:
            response = requests.get(self.base_url, timeout=self.default_timeout)
            logger.info(f"Test connection status: {response.status_code}")
            return {"status": "connected", "code": response.status_code}
        except RequestException as e:
            logger.error(f"Test connection failed: {e}")
            return {"status": "failed", "error": str(e)}

    def get_device_from_db(self, device_id):
        """
        Retrieve device details from the database using HardwareService.
        :param device_id: The unique ID of the device.
        :return: JSON response with device details.
        """
        logger.info(f"Fetching device {device_id} from database via HardwareService...")
        return HardwareService.get_device_from_db(device_id)

    def start_mqtt_communication(self, device):
        """
        Start MQTT communication for a given device.
        :param device: Dictionary containing device information.
        :return: True if successful, False otherwise.
        """
        if not device or not isinstance(device, dict) or "id" not in device:
            logger.error("Invalid device data: missing 'id'.")
            return False

        try:
            if not self.mqtt_service:
                logger.error("MQTT Service is not initialized.")
                return False

            # Ensure the MQTT connection is active
            self.mqtt_service.connect()
        
            # Subscribe to the device's MQTT topic
            topic = f"devices/{device['id']}/#"
            self.mqtt_service.subscribe(topic)

            logger.info(f"Successfully started MQTT communication for device {device['id']} on topic '{topic}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to start MQTT communication for device {device.get('id', 'UNKNOWN')}: {e}")
            return False



def create_api_manager(base_url, mqtt_broker=MQTT_BROKER):
    """
    Utility function to create an APIManager instance.
    :param base_url: Base URL of the API.
    :param mqtt_broker: MQTT broker address (defaults to environment variable).
    :return: APIManager instance.
    """
    # api_manager = APIManager(base_url, mqtt_broker)
    api_manager = create_api_manager(os.getenv("BASE_API_URL", f"http://{socket.gethostbyname(socket.gethostname())}:5000/api"),
                                 mqtt_broker=os.getenv("MQTT_BROKER", socket.gethostbyname(socket.gethostname())))


    return api_manager
