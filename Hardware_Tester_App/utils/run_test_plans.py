from HardwareTester.utils.api_manager import get_api_manager
from HardwareTester.utils.custom_logger import CustomLogger

import os
from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()

# Initialize Logger
logger = CustomLogger.get_logger("TestRunner")

# Initialize APIManager
api_manager = get_api_manager()

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
