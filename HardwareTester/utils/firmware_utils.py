
import hashlib
from HardwareTester.utils import custom_logger
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("FirmwareUtils")

def process_uploaded_firmware(file):
    """
    Process and store uploaded firmware.
    :param file: File object containing the firmware.
    :return: Firmware details.
    """
    try:
        firmware_data = file.read()
        firmware_hash = hashlib.sha256(firmware_data).hexdigest()
        logger.info(f"Firmware uploaded. Hash: {firmware_hash}")
        return {"hash": firmware_hash, "data": firmware_data}
    except Exception as e:
        logger.error(f"Error processing firmware: {e}")
        return {"error": str(e)}


def validate_firmware_file(firmware_path):
    """
    Validate firmware file for supported formats.
    :param firmware_path: Path to the firmware file.
    :return: SHA-256 hash of the file or None if invalid.
    """
    try:
        with open(firmware_path, "r") as f:
            firmware_data = f.read()

        if firmware_path.endswith(".txt"):
            logger.info("Validating text-based firmware file.")
        elif firmware_path.endswith(".bin") or firmware_path.endswith(".hex"):
            logger.error("Binary or hex firmware format detected. This script supports text-based firmware only.")
            return None
        else:
            logger.error("Unsupported firmware format.")
            return None

        firmware_hash = hashlib.sha256(firmware_data.encode('utf-8')).hexdigest()
        logger.info(f"Firmware validation successful. Hash: {firmware_hash}")
        return firmware_hash
    except Exception as e:
        logger.error(f"Failed to validate firmware file: {e}")
        return None


