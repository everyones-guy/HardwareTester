import os
from HardwareTester.utils.logger import Logger
from HardwareTester.utils.api_manager import create_api_manager

logger = Logger(name="TestService", log_file="logs/test_service.log", level="INFO")
api_manager = create_api_manager("https://example.com/api")

class TestService:
    @staticmethod
    def list_tests():
        """
        Fetch and return a list of all available tests (not limited to test plans).
        :return: List of available tests.
        """
        logger.info("Fetching list of available tests...")
        response = api_manager.get("tests")
        if "error" in response:
            logger.error(f"Failed to fetch tests: {response['error']}")
            return {"success": False, "error": response["error"]}
        logger.info(f"Retrieved {len(response.get('tests', []))} tests.")
        return {"success": True, "tests": response.get("tests", [])}

    @staticmethod
    def run_test(test_id, parameters=None):
        """
        Run a specific test by ID with optional parameters.
        :param test_id: ID of the test to execute.
        :param parameters: Optional parameters for test execution.
        :return: Execution results.
        """
        logger.info(f"Running test ID {test_id} with parameters: {parameters}...")
        payload = {"parameters": parameters} if parameters else {}
        response = api_manager.post(f"tests/{test_id}/run", payload=payload)
        if "error" in response:
            logger.error(f"Failed to run test {test_id}: {response['error']}")
            return {"success": False, "error": response["error"]}
        logger.info(f"Test executed successfully: {response}")
        return {"success": True, "results": response.get("results", [])}

    @staticmethod
    def stress_test(device_id, duration, load):
        """
        Perform a stress test on a device.
        :param device_id: ID of the target device.
        :param duration: Duration of the stress test (in seconds).
        :param load: Load level for the stress test (e.g., percentage or specific value).
        :return: Stress test results.
        """
        logger.info(f"Starting stress test on device {device_id} for {duration}s at {load}% load...")
        payload = {"duration": duration, "load": load}
        response = api_manager.post(f"devices/{device_id}/stress-test", payload=payload)
        if "error" in response:
            logger.error(f"Failed to perform stress test on device {device_id}: {response['error']}")
            return {"success": False, "error": response["error"]}
        logger.info(f"Stress test completed successfully: {response}")
        return {"success": True, "results": response.get("results", [])}

    @staticmethod
    def save_test_results(test_id, results):
        """
        Save the results of a test to the database or an external storage system.
        :param test_id: ID of the test.
        :param results: Results data to save.
        :return: Success or failure message.
        """
        logger.info(f"Saving results for test ID {test_id}...")
        try:
            file_path = os.path.join("results", f"test_{test_id}_results.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as file:
                file.write(results)
            logger.info(f"Results saved successfully to {file_path}.")
            return {"success": True, "message": f"Results saved to {file_path}."}
        except Exception as e:
            logger.error(f"Error saving test results: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def fetch_test_logs(test_id):
        """
        Fetch logs related to a specific test.
        :param test_id: ID of the test.
        :return: Logs for the specified test.
        """
        logger.info(f"Fetching logs for test ID {test_id}...")
        response = api_manager.get(f"tests/{test_id}/logs")
        if "error" in response:
            logger.error(f"Failed to fetch logs for test {test_id}: {response['error']}")
            return {"success": False, "error": response["error"]}
        logger.info(f"Logs retrieved successfully for test ID {test_id}.")
        return {"success": True, "logs": response.get("logs", [])}

    @staticmethod
    def validate_test_configuration(configuration):
        """
        Validate a test configuration before execution.
        :param configuration: Test configuration data.
        :return: Validation results.
        """
        logger.info("Validating test configuration...")
        response = api_manager.post("tests/validate-configuration", payload=configuration)
        if "error" in response:
            logger.error(f"Configuration validation failed: {response['error']}")
            return {"success": False, "error": response["error"]}
        logger.info("Configuration validated successfully.")
        return {"success": True, "validation": response.get("validation", {})}
