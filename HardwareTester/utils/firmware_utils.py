import os
import hashlib
import zipfile
import rpmfile
import shutil
import tempfile
from HardwareTester.utils.custom_logger import CustomLogger

logger = CustomLogger.get_logger("FirmwareUtils")


def extract_rpm(rpm_path, extract_dir):
    """
    Extracts an RPM package and retrieves firmware files.
    :param rpm_path: Path to the RPM package.
    :param extract_dir: Directory where the contents will be extracted.
    :return: List of extracted firmware files.
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        with rpmfile.open(rpm_path) as rpm:
            for member in rpm.getmembers():
                if member.isdir:
                    continue  # Skip directories
                file_path = os.path.join(extract_dir, member.name)
                with open(file_path, "wb") as f:
                    f.write(rpm.extractfile(member).read())
                logger.info(f"Extracted: {file_path}")
        return os.listdir(extract_dir)
    except Exception as e:
        logger.error(f"Failed to extract RPM: {e}")
        return []


def extract_img(img_path, extract_dir):
    """
    Extracts firmware files from an IMG file.
    :param img_path: Path to the IMG file.
    :param extract_dir: Directory to extract the contents.
    :return: List of extracted firmware files.
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(img_path, "r") as img_zip:
            img_zip.extractall(extract_dir)
            logger.info(f"Extracted {len(img_zip.namelist())} files from {img_path}.")
        return os.listdir(extract_dir)
    except zipfile.BadZipFile:
        logger.error("Invalid IMG format. Ensure it's a valid ZIP archive.")
        return []
    except Exception as e:
        logger.error(f"Failed to extract IMG: {e}")
        return []


def extract_zipped_firmware(zip_path, extract_dir):
    """
    Extracts a ZIP archive containing RPM or IMG firmware files.
    :param zip_path: Path to the ZIP archive.
    :param extract_dir: Directory to extract the contents.
    :return: List of extracted firmware files.
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
            logger.info(f"Extracted ZIP archive: {zip_path}")
        return os.listdir(extract_dir)
    except zipfile.BadZipFile:
        logger.error("Invalid ZIP format.")
        return []
    except Exception as e:
        logger.error(f"Failed to extract ZIP: {e}")
        return []


def process_firmware_package(firmware_path):
    """
    Determines the type of firmware package and extracts/validates it.
    :param firmware_path: Path to the firmware file (.rpm, .img, or .zip).
    :return: List of extracted firmware files.
    """
    temp_dir = tempfile.mkdtemp()
    extracted_files = []

    if firmware_path.endswith(".rpm"):
        extracted_files = extract_rpm(firmware_path, temp_dir)
    elif firmware_path.endswith(".img"):
        extracted_files = extract_img(firmware_path, temp_dir)
    elif firmware_path.endswith(".zip"):
        extracted_files = extract_zipped_firmware(firmware_path, temp_dir)
    else:
        logger.error("Unsupported firmware format.")
        return None

    if not extracted_files:
        return None

    # Process extracted firmware files (hash check, validation, etc.)
    for filename in extracted_files:
        file_path = os.path.join(temp_dir, filename)
        firmware_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
        logger.info(f"Processed firmware: {filename} (SHA-256: {firmware_hash})")

    return extracted_files


# Example Usage
if __name__ == "__main__":
    firmware_files = process_firmware_package("test_firmware.zip")  # Change to your file path
    print(f"Extracted firmware files: {firmware_files}")
