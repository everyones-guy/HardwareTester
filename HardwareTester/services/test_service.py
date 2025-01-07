import os
import json
from HardwareTester.extensions import logger
from HardwareTester.utils.api_manager import create_api_manager

# Initialize API manager
api_manager = create_api_manager("https://example.com/api")


class TestService:
    """Service for managing and executing tests."""

    @staticmethod
    def list_tests() -> dict:
        """
        Fetch and return a list of all available tests (not limited to test plans).
        :return: Dictionary containing tests or an error message.
        """
        logger.info("Fetching list of available tests...")
        try:
            response = api_manager.get("tests")
            if "error" in response:
                logger.error(f"Failed to fetch tests: {response['error']}")
                return {"success": False, "error": response["error"]}
            tests = response.get("tests", [])
            logger.info(f"Retrieved {len(tests)} tests.")
            return {"success": True, "tests": tests}
        except Exception as e:
            logger.error(f"Unexpected error fetching tests: {e}")
            return {"success": False, "error": "An unexpected error occurred while fetching tests."}

    @staticmethod
    def run_test(test_id: int, parameters: dict = None) -> dict:
        """
        Run a specific test by ID with optional parameters.
        :param test_id: ID of the test to execute.
        :param parameters: Optional parameters for test execution.
        :return: Execution results or an error message.
        """
        logger.info(f"Running test ID {test_id} with parameters: {parameters}...")
        try:
            payload = {"parameters": parameters} if parameters else {}
            response = api_manager.post(f"tests/{test_id}/run", payload=payload)
            if "error" in response:
                logger.error(f"Failed to run test {test_id}: {response['error']}")
                return {"success": False, "error": response["error"]}
            logger.info(f"Test executed successfully: {response}")
            return {"success": True, "results": response.get("results", [])}
        except Exception as e:
            logger.error(f"Unexpected error running test {test_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred while running the test."}

    @staticmethod
    def stress_test(device_id: int, duration: int, load: int) -> dict:
        """
        Perform a stress test on a device.
        :param device_id: ID of the target device.
        :param duration: Duration of the stress test (in seconds).
        :param load: Load level for the stress test (percentage or specific value).
        :return: Stress test results or an error message.
        """
        logger.info(f"Starting stress test on device {device_id} for {duration}s at {load}% load...")
        try:
            payload = {"duration": duration, "load": load}
            response = api_manager.post(f"devices/{device_id}/stress-test", payload=payload)
            if "error" in response:
                logger.error(f"Failed to perform stress test on device {device_id}: {response['error']}")
                return {"success": False, "error": response["error"]}
            logger.info(f"Stress test completed successfully: {response}")
            return {"success": True, "results": response.get("results", [])}
        except Exception as e:
            logger.error(f"Unexpected error during stress test on device {device_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred during the stress test."}

    @staticmethod
    def save_test_results(test_id: int, results: dict) -> dict:
        """
        Save the results of a test to a file.
        :param test_id: ID of the test.
        :param results: Results data to save.
        :return: Success or error message.
        """
        logger.info(f"Saving results for test ID {test_id}...")
        try:
            file_path = os.path.join("results", f"test_{test_id}_results.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as file:
                json.dump(results, file, indent=4)
            logger.info(f"Results saved successfully to {file_path}.")
            return {"success": True, "message": f"Results saved to {file_path}."}
        except Exception as e:
            logger.error(f"Error saving test results for test ID {test_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def fetch_test_logs(test_id: int) -> dict:
        """
        Fetch logs related to a specific test.
        :param test_id: ID of the test.
        :return: Logs for the specified test or an error message.
        """
        logger.info(f"Fetching logs for test ID {test_id}...")
        try:
            response = api_manager.get(f"tests/{test_id}/logs")
            if "error" in response:
                logger.error(f"Failed to fetch logs for test {test_id}: {response['error']}")
                return {"success": False, "error": response["error"]}
            logs = response.get("logs", [])
            logger.info(f"Logs retrieved successfully for test ID {test_id}.")
            return {"success": True, "logs": logs}
        except Exception as e:
            logger.error(f"Unexpected error fetching logs for test ID {test_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred while fetching logs."}

    @staticmethod
    def validate_test_configuration(configuration: dict) -> dict:
        """
        Validate a test configuration before execution.
        :param configuration: Test configuration data.
        :return: Validation results or an error message.
        """
        logger.info("Validating test configuration...")
        try:
            response = api_manager.post("tests/validate-configuration", payload=configuration)
            if "error" in response:
                logger.error(f"Configuration validation failed: {response['error']}")
                return {"success": False, "error": response["error"]}
            logger.info("Configuration validated successfully.")
            return {"success": True, "validation": response.get("validation", {})}
        except Exception as e:
            logger.error(f"Unexpected error validating configuration: {e}")
            return {"success": False, "error": "An unexpected error occurred during configuration validation."}
