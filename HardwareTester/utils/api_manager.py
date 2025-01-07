
import requests
from requests.exceptions import RequestException
from HardwareTester.extensions import logger

class APIManager:
    """Library for managing API connections and requests."""

    def __init__(self, base_url, default_timeout=30):
        """
        Initialize the API Manager.
        :param base_url: Base URL of the API.
        :param default_timeout: Default timeout for requests in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout
        logger.info(f"APIManager initialized with base URL: {self.base_url}")

    def _log_request(self, method, endpoint, payload=None, headers=None):
        """Log request details."""
        logger.debug(f"Request Method: {method}")
        logger.debug(f"Endpoint: {endpoint}")
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
            return {"error": str(e)}

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
            return {"error": str(e)}

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
            return {"error": str(e)}

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
            return {"error": str(e)}

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


# Utility function to create an APIManager instance with dynamic base URL
def create_api_manager(base_url):
    """
    Utility function to create an APIManager instance.
    :param base_url: Base URL of the API.
    :return: APIManager instance.
    """
    return APIManager(base_url=base_url)

