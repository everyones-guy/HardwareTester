
import serial
import json
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SerialComm")

DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # Seconds between retries


class SerialComm:
    def __init__(self, port, baudrate=9600, timeout=1, retries=DEFAULT_RETRY_COUNT):
        """
        Initialize Serial Communication.
        :param port: Serial port name (e.g., COM3, /dev/ttyUSB0).
        :param baudrate: Baud rate for communication (default: 9600).
        :param timeout: Read timeout in seconds (default: 1).
        :param retries: Number of retries for communication errors (default: 3).
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self.connection = None

    def connect(self):
        """
        Establishes a serial connection.
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
        Closes the serial connection.
        """
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from {self.port}.")

    def send_data(self, data):
        """
        Sends data over the serial connection.
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

            self.connection.write(data.encode('utf-8'))
            logger.info(f"Data sent successfully: {data}")
            return {"success": True, "message": "Data sent successfully."}
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return {"success": False, "error": str(e)}

    def read_data(self):
        """
        Reads data from the serial connection.
        :return: Dictionary with data or error message.
        """
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return {"success": False, "error": "Serial connection is not open."}

        for attempt in range(1, self.retries + 1):
            try:
                raw_data = self.connection.readline().decode('utf-8').strip()
                logger.info(f"Raw data received: {raw_data}")

                # Try parsing as JSON; fallback to raw data if parsing fails
                try:
                    parsed_data = json.loads(raw_data)
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

    def discover_device(self):
        """
        Sends a discovery command to the connected device.
        :return: Dictionary with device info or error message.
        """
        discovery_command = '{"action": "discover"}'  # Example discovery command
        self.send_data(discovery_command)

        response = self.read_data()
        if response.get("success"):
            logger.info("Device discovery successful.")
            return {"success": True, "device_info": response["data"]}
        else:
            logger.error("Device discovery failed.")
            return {"success": False, "error": response.get("error", "Unknown error.")}


if __name__ == "__main__":
    # Example usage
    comm = SerialComm(port="COM3", baudrate=9600, timeout=2, retries=3)

    try:
        comm.connect()
        # Send a sample command
        response = comm.send_data({"command": "get_status"})
        logger.info(f"Send Data Response: {response}")

        # Read response from the device
        response = comm.read_data()
        logger.info(f"Read Data Response: {response}")

        # Discover device
        discovery = comm.discover_device()
        logger.info(f"Discovery Response: {discovery}")
    finally:
        comm.disconnect()

