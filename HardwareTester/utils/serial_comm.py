import serial
import hashlib
import json
import time
import serial.tools.list_ports
from HardwareTester.extensions import logger
from HardwareTester.utils.centralized_logger import CentralizedLogger

logger = CentralizedLogger.getLogger("serial_comm")  # Use a specific name for this module's logger


#logger = logger.getLogger(__name__)

# Set up logging
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # Seconds between retries

class SerialComm:
    def __init__(self, port=None, baudrate=9600, timeout=1, retries=DEFAULT_RETRY_COUNT, debug=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self.connection = None
        self.debug = debug

        if self.debug:
            logger.setLevel("DEBUG")

    def connect(self):
        if not self.port:
            self.port = self.find_comm_port()
            if not self.port:
                LoggerUtils.log_error("No suitable COM port found.")
                raise serial.SerialException("No suitable COM port found.")

        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            LoggerUtils.log_info(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            LoggerUtils.log_error(f"Failed to connect to {self.port}: {e}")
            raise e

    def disconnect(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            LoggerUtils.log_info(f"Disconnected from {self.port}.")

    def discover_device(self, timeout=5):
        """
        Discover a connected device by scanning serial ports, sending a discovery command,
        and prompting for credentials or additional info if needed.
        """
        LoggerUtils.log_info("Scanning for serial devices...")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            try:
                LoggerUtils.log_info(f"Probing port: {port.device}")
                with serial.Serial(port.device, self.baudrate, timeout=self.timeout) as ser:
                    ser.write(b'{"action": "discover"}\n')
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        response = ser.readline().decode("utf-8").strip()
                        if response:
                            try:
                                data = json.loads(response)
                                LoggerUtils.log_info(f"Device discovered on {port.device}: {data}")

                                # Prompt for additional input
                                credentials = self.get_credentials()
                                data["credentials"] = credentials
                                return {"success": True, "port": port.device, "device_info": data}
                            except json.JSONDecodeError:
                                LoggerUtils.log_warning(f"Non-JSON response received on {port.device}: {response}")
                                continue
            except (serial.SerialException, serial.SerialTimeoutException) as e:
                LoggerUtils.log_warning(f"Failed to probe port {port.device}: {e}")
        LoggerUtils.log_error("No devices discovered.")
        return {"success": False, "error": "No devices discovered."}

    def get_credentials(self):
        """
        Prompt the user for credentials or additional information.
        :return: A dictionary containing the entered credentials.
        """
        print("Enter device credentials:")
        username = input("Username: ")
        password = input("Password: ")
        return {"username": username, "password": password}

    def find_comm_port(self):
        LoggerUtils.log_info("Searching for COM ports...")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            LoggerUtils.log_info(f"Found port: {port.device} - {port.description}")
            if "USB" in port.description or "Serial" in port.description:
                LoggerUtils.log_info(f"Using port: {port.device}")
                return port.device
        LoggerUtils.log_error("No suitable USB or Serial COM port found.")
        return None
