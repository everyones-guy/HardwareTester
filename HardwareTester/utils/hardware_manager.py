import platform
import psutil
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ValveController:
    """Class to manage interactions with a valve via API."""
    def __init__(self, api_url, auth_token=None):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    def get_status(self):
        """Retrieve the current status of the valve."""
        try:
            response = requests.get(f"{self.api_url}/status", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching valve status: {e}")
            return {"error": str(e)}

    def send_command(self, command, payload=None):
        """Send a command to the valve."""
        try:
            payload = payload or {}
            response = requests.post(f"{self.api_url}/{command}", json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error sending command '{command}': {e}")
            return {"error": str(e)}

def get_system_info():
    """Retrieve system information."""
    return {
        "Platform": platform.system(),
        "Platform-Version": platform.version(),
        "Architecture": platform.architecture()[0],
        "CPU Cores": psutil.cpu_count(logical=True),
        "Memory (GB)": psutil.virtual_memory().total // (1024**3),
    }

def print_system_info():
    """Print system information in a readable format."""
    info = get_system_info()
    print("System Information:")
    for key, value in info.items():
        print(f"{key}: {value}")

def manage_valve(api_url, command, payload=None, auth_token=None):
    """
    Utility function to manage valve operations.
    :param api_url: Base API URL of the valve.
    :param command: Command to send to the valve (e.g., 'open', 'close', 'adjust').
    :param payload: Data payload for the command (optional).
    :param auth_token: Authentication token for the API (optional).
    :return: Result of the operation.
    """
    valve = ValveController(api_url, auth_token)
    if command == "status":
        return valve.get_status()
    return valve.send_command(command, payload)

def simulate_valve_actions(valve_simulator):
    """
    Simulate valve actions for testing purposes.
    :param valve_simulator: A mock function or class simulating valve behavior.
    :return: Simulation results.
    """
    logging.info("Simulating valve actions...")
    try:
        actions = ["open", "adjust", "close"]
        results = {action: valve_simulator(action) for action in actions}
        logging.info(f"Simulation results: {results}")
        return results
    except Exception as e:
        logging.error(f"Simulation failed: {e}")
        return {"error": str(e)}
