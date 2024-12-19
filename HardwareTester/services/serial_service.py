import serial
import logging

logger = logging.getLogger(__name__)

class SerialService:
    def __init__(self, port, baudrate=9600, timeout=1):
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

    def connect(self):
        """Establish the serial connection."""
        try:
            self.connection = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            raise e

    def disconnect(self):
        """Close the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from {self.port}.")

    def send_data(self, data):
        """Send data to the device."""
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return False
        try:
            self.connection.write(data.encode())
            logger.info(f"Sent data: {data}")
            return True
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return False

    def read_data(self):
        """Read data from the device."""
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return None
        try:
            data = self.connection.readline().decode().strip()
            logger.info(f"Received data: {data}")
            return data
        except Exception as e:
            logger.error(f"Failed to read data: {e}")
            return None
