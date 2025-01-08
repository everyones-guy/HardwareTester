#serial_comm.py

import serial
import json
from HardwareTester.utils import Logger
import time

logger = Logger.getLogger(__name__)

# Set up logging
#logger.getLogger("SerialComm")

DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # Seconds between retries


class SerialComm:
    def __init__(self, port, baudrate=9600, timeout=1, retries=DEFAULT_RETRY_COUNT, debug=False):
        """
        Initialize Serial Communication.
        :param port: Serial port name (e.g., COM3, /dev/ttyUSB0).
        :param baudrate: Baud rate for communication (default: 9600).
        :param timeout: Read timeout in seconds (default: 1).
        :param retries: Number of retries for communication errors (default: 3).
        :param debug: Enables verbose logging if True (default: False).
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self.connection = None
        self.debug = debug

        if self.debug:
            logger.setLevel("DEBUG")

    def connect(self):
        """
        Establish a serial connection.
        """
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,

            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            raise e

    def disconnect(self):
        """
        Close the serial connection.
        """
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from {self.port}.")

    def send_data(self, data):
        """
        Send data over the serial connection.
        :param data: Data to send (string or JSON).
        :return: Dictionary with success or error message.
        """
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return {"success": False, "error": "Serial connection is not open."}

        try:
            if isinstance(data, (dict, list)):
                data = json.dumps(data)  # Convert JSON to string
            if not isinstance(data, str):
                raise ValueError("Data must be a string or JSON serializable object.")

            if self.debug:
                logger.debug(f"Sending: {data}")

            self.connection.write(data.encode("utf-8"))
            logger.info(f"Data sent successfully: {data}")
            return {"success": True, "message": "Data sent successfully."}
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return {"success": False, "error": str(e)}

    def read_data(self):
        """
        Read data from the serial connection.
        :return: Dictionary with data or error message.
        """
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return {"success": False, "error": "Serial connection is not open."}

        for attempt in range(1, self.retries + 1):
            try:
                raw_data = self.connection.readline().decode("utf-8").strip()
                if self.debug:
                    logger.debug(f"Raw data received: {raw_data}")

                # Try parsing as JSON; fallback to raw data if parsing fails
                try:
                    parsed_data = json.loads(raw_data)
                    logger.info("Data received successfully.")
                    return {"success": True, "data": parsed_data}
                except json.JSONDecodeError:
                    logger.warning("Data received is not in JSON format.")
                    return {"success": True, "data": {"raw": raw_data}}

            except serial.SerialTimeoutException:
                logger.warning(f"Timeout occurred on attempt {attempt} while reading.")
                time.sleep(DEFAULT_RETRY_DELAY)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return {"success": False, "error": str(e)}

        logger.error(f"All {self.retries} attempts to read data failed.")
        return {"success": False, "error": "Failed to read data after retries."}

    def discover_device(self, timeout=5):
        """
        Send a discovery command to the connected device.
        :param timeout: Timeout for the discovery process (default: 5 seconds).
        :return: Dictionary with device info or error message.
        """
        discovery_command = '{"action": "discover"}'  # Example discovery command
        self.send_data(discovery_command)

        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.read_data()
            if response.get("success"):
                logger.info("Device discovery successful.")
                return {"success": True, "device_info": response["data"]}
            time.sleep(0.5)  # Short delay before retrying

        logger.error("Device discovery timed out.")
        return {"success": False, "error": "Device discovery timed out."}

    def test_connection(self):
        """
        Test the serial connection.
        :return: Dictionary with connection status.
        """
        if not self.connection or not self.connection.is_open:
            return {"success": False, "message": "No active serial connection."}

        try:
            self.connection.write(b"PING")
            time.sleep(1)
            response = self.connection.readline().decode("utf-8").strip()
            if response == "PONG":
                return {"success": True, "message": "Connection is active."}
            return {"success": False, "message": "Unexpected response from device."}
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {"success": False, "message": str(e)}


#if __name__ == "__main__":
#    # Example usage
#    comm = SerialComm(port="COM3", baudrate=9600, timeout=2, retries=3, debug=True)

#    try:
#        comm.connect()

#        # Test connection
#        test_result = comm.test_connection()
#        logger.info(f"Connection Test: {test_result}")
#
#        # Send a sample command
#        response = comm.send_data({"command": "get_status"})
#        logger.info(f"Send Data Response: {response}")
#
#        # Read response from the device
#        response = comm.read_data()
#        logger.info(f"Read Data Response: {response}")
#
#        # Discover device
#        discovery = comm.discover_device(timeout=5)
#        logger.info(f"Discovery Response: {discovery}")
#    finally:
#        comm.disconnect()
