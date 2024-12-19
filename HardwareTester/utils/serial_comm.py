import serial
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SerialComm")

def read_serial_data(port, baudrate=9600, timeout=1):
    """
    Reads data from a serial port.
    
    Args:
        port (str): Serial port name (e.g., COM3, /dev/ttyUSB0).
        baudrate (int): Baud rate for communication (default: 9600).
        timeout (int): Timeout in seconds (default: 1).

    Returns:
        dict: Parsed JSON data or an error message.
    """
    try:
        logger.info(f"Attempting to read from port {port} at {baudrate} baud.")
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            raw_data = ser.readline().decode('utf-8').strip()
            logger.info(f"Raw data received: {raw_data}")
            try:
                return json.loads(raw_data)  # Attempt to parse as JSON
            except json.JSONDecodeError:
                logger.warning("Data received is not in JSON format.")
                return {"raw_data": raw_data}
    except serial.SerialException as e:
        logger.error(f"Serial communication error: {e}")
        return {"error": f"Serial communication error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {e}"}

def send_serial_data(port, data, baudrate=9600, timeout=1):
    """
    Sends data to a serial port.
    
    Args:
        port (str): Serial port name (e.g., COM3, /dev/ttyUSB0).
        data (str): Data to send (will be encoded to bytes).
        baudrate (int): Baud rate for communication (default: 9600).
        timeout (int): Timeout in seconds (default: 1).

    Returns:
        dict: Success message or an error message.
    """
    try:
        logger.info(f"Attempting to send data to port {port} at {baudrate} baud.")
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            ser.write(data.encode('utf-8'))
            logger.info(f"Data sent successfully: {data}")
            return {"success": True, "message": "Data sent successfully."}
    except serial.SerialException as e:
        logger.error(f"Serial communication error: {e}")
        return {"error": f"Serial communication error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {e}"}
