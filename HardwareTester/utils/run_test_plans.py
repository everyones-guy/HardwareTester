from HardwareTester.utils.api_manager import create_api_manager
from HardwareTester.utils.logger import Logger

# Initialize Logger
logger = Logger(name="TestRunner", log_file="logs/test_runner.log", level="INFO")

# Initialize APIManager
api_manager = create_api_manager("https://example.com/api")

def run_test_plan(test_plan_id):
    """Run a test plan."""
    logger.info(f"Running test plan ID {test_plan_id}...")
    response = api_manager.post(f"test-plans/{test_plan_id}/run")
    if "error" in response:
        logger.error(f"Failed to run test plan {test_plan_id}: {response['error']}")
        return
    logger.info(f"Test plan executed successfully: {response}")
    print(f"Execution Results: {response}")

if __name__ == "__main__":
    run_test_plan(1)
