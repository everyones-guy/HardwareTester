import os
import hashlib
import zipfile
import rpmfile
import shutil
import tempfile
import subprocess
import glob
from HardwareTester.utils.custom_logger import CustomLogger

logger = CustomLogger.get_logger("FirmwareUtils")


def extract_rpm(rpm_path, extract_dir):
    """
    Extracts an RPM package and retrieves files.
    If a CPIO file is found, it will be extracted next.
    :param rpm_path: Path to the RPM package.
    :param extract_dir: Directory where the contents will be extracted.
    :return: Path to extracted files.
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

        # Look for a CPIO file inside the extracted RPM contents
        cpio_files = glob.glob(os.path.join(extract_dir, "*.cpio"))
        if cpio_files:
            logger.info(f"CPIO file found: {cpio_files[0]}. Extracting now...")
            return extract_cpio(cpio_files[0], extract_dir)
        else:
            logger.warning("No CPIO file found inside the RPM.")
            return extract_dir

    except Exception as e:
        logger.error(f"Failed to extract RPM: {e}")
        return None


def extract_cpio(cpio_path, extract_dir):
    """
    Extracts a CPIO archive.
    Handles cases where an empty folder is created inside the extracted contents.
    :param cpio_path: Path to the CPIO archive.
    :param extract_dir: Directory where the contents will be extracted.
    :return: Path to extracted source code files.
    """
    try:
        subprocess.run(["7z", "x", cpio_path, f"-o{extract_dir}"], check=True)
        logger.info(f"Extracted CPIO to {extract_dir}")

        # Check if the actual content is inside an extra empty folder
        extracted_files = os.listdir(extract_dir)
        if len(extracted_files) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_files[0])):
            nested_dir = os.path.join(extract_dir, extracted_files[0])
            logger.info(f"Detected nested structure in CPIO: Moving contents of {nested_dir}")
            for file in os.listdir(nested_dir):
                shutil.move(os.path.join(nested_dir, file), extract_dir)

        return extract_dir

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract CPIO: {e}")
        return None


def extract_img(img_path, extract_dir):
    """
    Extracts firmware files from an IMG file.
    :param img_path: Path to the IMG file.
    :param extract_dir: Directory to extract the contents.
    :return: Path to extracted files.
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(img_path, "r") as img_zip:
            img_zip.extractall(extract_dir)
            logger.info(f"Extracted {len(img_zip.namelist())} files from {img_path}.")
        return extract_dir
    except zipfile.BadZipFile:
        logger.error("Invalid IMG format. Ensure it's a valid ZIP archive.")
        return None
    except Exception as e:
        logger.error(f"Failed to extract IMG: {e}")
        return None


def extract_zipped_firmware(zip_path, extract_dir):
    """
    Extracts a ZIP archive containing RPM or IMG firmware files.
    :param zip_path: Path to the ZIP archive.
    :param extract_dir: Directory to extract the contents.
    :return: Path to extracted files.
    """
    try:
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
            logger.info(f"Extracted ZIP archive: {zip_path}")
        return extract_dir
    except zipfile.BadZipFile:
        logger.error("Invalid ZIP format.")
        return None
    except Exception as e:
        logger.error(f"Failed to extract ZIP: {e}")
        return None


def find_source_files(directory, extensions=(".cs", ".cpp", ".h", ".py")):
    """
    Recursively find source code files in the extracted directory.
    Filters out config files.
    :param directory: Directory to search.
    :param extensions: File extensions to look for.
    :return: List of source code files.
    """
    source_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions) and not file.endswith((".conf", ".ini")):
                source_files.append(os.path.join(root, file))
    return source_files


def process_firmware_package(firmware_path):
    """
    Determines the type of firmware package and extracts/validates it.
    :param firmware_path: Path to the firmware file (.rpm, .img, .zip).
    :return: List of extracted source code files.
    """
    temp_dir = tempfile.mkdtemp()
    extracted_dir = None

    if firmware_path.endswith(".rpm"):
        extracted_dir = extract_rpm(firmware_path, temp_dir)
    elif firmware_path.endswith(".img"):
        extracted_dir = extract_img(firmware_path, temp_dir)
    elif firmware_path.endswith(".zip"):
        extracted_dir = extract_zipped_firmware(firmware_path, temp_dir)
    else:
        logger.error("Unsupported firmware format.")
        return None

    if not extracted_dir:
        logger.error("Extraction failed.")
        return None

    # Locate and return relevant source files
    source_files = find_source_files(extracted_dir)

    if not source_files:
        logger.info("No source files found in extracted firmware.")
        return None

    return source_files


# Example Usage
if __name__ == "__main__":
    firmware_files = process_firmware_package("test_firmware.rpm")  # Change to your file path
    print(f"Extracted firmware files: {firmware_files}")
