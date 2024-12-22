import hashlib
import logging

logger = logging.getLogger("FirmwareUtils")

def validate_firmware_file(firmware_path):
    """
    Validate firmware file for supported formats.
    :param firmware_path: Path to the firmware file.
    :return: SHA-256 hash of the file or None if invalid.
    """
    try:
        with open(firmware_path, "rb") as f:
            firmware_data = f.read()

        if firmware_path.endswith(".bin"):
            logger.info("Validating binary firmware file.")
        elif firmware_path.endswith(".hex"):
            logger.info("Validating hex firmware file.")
            firmware_data = bytes.fromhex(firmware_data.decode())
        elif firmware_path.endswith(".txt"):
            logger.info("Validating text-based firmware file.")
        else:
            logger.error("Unsupported firmware format.")
            return None

        firmware_hash = hashlib.sha256(firmware_data).hexdigest()
        logger.info(f"Firmware validation successful. Hash: {firmware_hash}")
        return firmware_hash
    except Exception as e:
        logger.error(f"Failed to validate firmware file: {e}")
        return None
