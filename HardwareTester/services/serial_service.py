# serial_service.py

import serial
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("serial_service")

class SerialService:
    """Service for managing serial communication."""

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize the serial service.
        :param port: Serial port (e.g., COM3 on Windows or /dev/ttyUSB0 on Linux).
        :param baudrate: Communication speed.
        :param timeout: Read timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None

    def connect(self) -> bool:
        """
        Establish the serial connection.
        :return: True if the connection is successful, False otherwise.
        """
        try:
            self.connection = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud.")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """Close the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from {self.port}.")

    def reconnect(self) -> bool:
        """
        Reconnect to the serial port.
        :return: True if the reconnection is successful, False otherwise.
        """
        self.disconnect()
        logger.info(f"Attempting to reconnect to {self.port}...")
        return self.connect()

    def send_data(self, data: str) -> bool:
        """
        Send data to the device.
        :param data: String data to send.
        :return: True if the data is sent successfully, False otherwise.
        """
        if not self.connection or not self.connection.is_open:
            logger.warning("Serial connection is not open. Attempting to reconnect...")
            if not self.reconnect():
                return False

        try:
            self.connection.write(data.encode())
            logger.info(f"Sent data: {data}")
            return True
        except serial.SerialException as e:
            logger.error(f"Serial error while sending data: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while sending data: {e}")
            return False

    def read_data(self):
        """
        Read data from the serial connection.
        :return: Dictionary with parsed data or error message.
        """
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return {"success": False, "error": "Serial connection is not open."}

        for attempt in range(1, self.retries + 1):
            try:
                raw_data = self.connection.readline().decode("utf-8").strip()
                if self.debug:
                    logger.debug(f"Raw data received: {raw_data}")

                # Attempt to parse the raw data
                parsed_data = self.parse_raw_data(raw_data)
                if parsed_data:
                    logger.info("Data received and parsed successfully.")
                    return {"success": True, "data": parsed_data}
                else:
                    logger.warning("Failed to parse raw data.")
                    return {"success": True, "data": {"raw": raw_data}}

            except serial.SerialTimeoutException:
                logger.warning(f"Timeout occurred on attempt {attempt} while reading.")
                time.sleep(DEFAULT_RETRY_DELAY)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return {"success": False, "error": str(e)}

        logger.error(f"All {self.retries} attempts to read data failed.")
        return {"success": False, "error": "Failed to read data after retries."}

    def parse_raw_data(self, raw_data):
        """
        Parse raw data into a structured format.
        :param raw_data: Raw data string.
        :return: Parsed data as a dictionary or None if parsing fails.
        """
        try:
            # Example: Parse key=value pairs separated by semicolons
            data = {}
            pairs = raw_data.split(";")
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    data[key.strip()] = value.strip()
            return data if data else None
        except Exception as e:
            logger.error(f"Failed to parse raw data: {e}")
            return None


    def is_connected(self) -> bool:
        """
        Check if the serial connection is open.
        :return: True if the connection is open, False otherwise.
        """
        return self.connection and self.connection.is_open

    def __enter__(self):
        """Context manager entry."""
        if not self.connect():
            raise serial.SerialException(f"Failed to connect to {self.port}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Usage:
#from HardwareTester.services.serial_service import SerialService

#port = "COM3"  # Update with your serial port
#baudrate = 9600

#with SerialService(port, baudrate) as serial_service:
#    if serial_service.is_connected():
#        serial_service.send_data("Test Command")
#        response = serial_service.read_data()
#        print(f"Response: {response}")
#    else:
#        print("Failed to connect to the serial port.")
        
# Usage Manual:
#serial_service = SerialService(port="COM3", baudrate=9600)

#if serial_service.connect():
#    serial_service.send_data("Test Command")
#    response = serial_service.read_data()
#    print(f"Response: {response}")
#    serial_service.disconnect()
#else:
#    print("Failed to connect to the serial port.")
        