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

    def reconnect(self):
        """Reconnect to the serial port."""
        self.disconnect()
        logger.info(f"Attempting to reconnect to {self.port}...")
        self.connect()

    def send_data(self, data):
        """
        Send data to the device.
        :param data: String data to send.
        :return: True if successful, False otherwise.
        """
        if not self.connection or not self.connection.is_open:
            logger.warning("Serial connection is not open. Attempting to reconnect...")
            self.reconnect()
        try:
            self.connection.write(data.encode())
            logger.info(f"Sent data: {data}")
            return True
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return False

    def read_data(self):
        """
        Read data from the device.
        :return: Decoded data as a string, or None if an error occurred.
        """
        if not self.connection or not self.connection.is_open:
            logger.warning("Serial connection is not open. Attempting to reconnect...")
            self.reconnect()
        try:
            data = self.connection.readline().decode().strip()
            logger.info(f"Received data: {data}")
            return data
        except Exception as e:
            logger.error(f"Failed to read data: {e}")
            return None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    port = "COM3"  # Update with your serial port
    baudrate = 9600

    with SerialService(port, baudrate) as serial_service:
        serial_service.send_data("Test Command")
        response = serial_service.read_data()
        print(f"Response: {response}")
