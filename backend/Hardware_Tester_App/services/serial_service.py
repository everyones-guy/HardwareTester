import stat
import serial
import time
import serial.tools.list_ports
from Hardware_Tester_App.utils.custom_logger import CustomLogger

logger = CustomLogger.get_logger("serial_service")

DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # Seconds between retries


class SerialService:
    def __init__(self, port=None, baudrate=9600, timeout=1, retries=DEFAULT_RETRY_COUNT, debug=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self.connection = None
        self.debug = debug

        if self.debug:
            logger.setLevel("DEBUG")

    @staticmethod
    def connect(self):
        if not self.port:
            self.port = self.find_comm_port()
            if not self.port:
                logger.error("No suitable COM port found.")
                raise serial.SerialException("No suitable COM port found.")

        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud.")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False

    @staticmethod
    def disconnect(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from {self.port}.")

    @staticmethod
    def reconnect(self):
        self.disconnect()
        logger.info(f"Attempting to reconnect to {self.port}...")
        return self.connect()
    
    @staticmethod
    def send_data(self, data):
        if not self.connection or not self.connection.is_open:
            logger.warning("Serial connection is not open. Attempting to reconnect...")
            if not self.reconnect():
                return False

        try:
            self.connection.write(data.encode())
            logger.info(f"Sent data: {data}")
            return True
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False

    @staticmethod
    def read_data(self):
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open.")
            return None

        for attempt in range(self.retries):
            try:
                data = self.connection.readline().decode("utf-8").strip()
                logger.debug(f"Raw data received: {data}")
                return data
            except serial.SerialTimeoutException:
                logger.warning(f"Timeout occurred on attempt {attempt + 1}. Retrying...")
                time.sleep(DEFAULT_RETRY_DELAY)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None

        logger.error(f"All {self.retries} attempts to read data failed.")
        return None

    @staticmethod
    def find_comm_port(self):
        logger.info("Searching for COM ports...")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            logger.info(f"Found port: {port.device} - {port.description}")
            if "USB" in port.description or "Serial" in port.description:
                return port.device
        logger.error("No suitable USB or Serial COM port found.")
        return None

    @staticmethod
    def discover_device(self, timeout=5):
        logger.info("Scanning for serial devices...")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            try:
                logger.info(f"Probing port: {port.device}")
                with serial.Serial(port.device, self.baudrate, timeout=self.timeout) as ser:
                    ser.write(b'{"action": "discover"}\n')
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        response = ser.readline().decode("utf-8").strip()
                        if response:
                            logger.info(f"Device discovered on {port.device}: {response}")
                            return {"port": port.device, "data": response}
            except Exception as e:
                logger.warning(f"Failed to probe port {port.device}: {e}")

        logger.error("No devices discovered.")
        return None

    @staticmethod
    def configure_device(self, baudrate=9600, parity="N", stopbits=1, databits=8):
        """
        Configure the serial device with the provided settings.
        :param baudrate: Communication speed.
        :param parity: Parity setting ('N', 'E', 'O', etc.).
        :param stopbits: Number of stop bits (1, 1.5, 2).
        :param databits: Number of data bits (5, 6, 7, 8).
        :return: True if configuration is successful, False otherwise.
        """
        if not self.connection or not self.connection.is_open:
            logger.error("Serial connection is not open. Unable to configure device.")
            return False

        try:
            # Update the serial connection settings
            self.connection.baudrate = baudrate
            self.connection.parity = getattr(serial, f"PARITY_{parity.upper()}", serial.PARITY_NONE)
            self.connection.stopbits = stopbits
            self.connection.bytesize = databits

            logger.info(
                f"Configured device with baudrate={baudrate}, parity={parity}, stopbits={stopbits}, databits={databits}."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to configure device: {e}")
            return False
    
    def __enter__(self):
        if not self.connect():
            raise serial.SerialException(f"Failed to connect to {self.port}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
