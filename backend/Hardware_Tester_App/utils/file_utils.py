import os
import shutil
import hashlib
import logging
import mimetypes
from pathlib import Path
from werkzeug.utils import secure_filename

logger = logging.getLogger("FileUtils")

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {"txt", "log", "json", "xml", "csv", "py", "cpp", "cs", "js"}

# Base directory for secure file storage
SAFE_STORAGE_PATH = Path("uploads").resolve()

# Ensure the storage directory exists
SAFE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

def is_safe_path(base_path, target_path):
    """
    Prevents directory traversal by ensuring the target path is within the base path.
    """
    return Path(target_path).resolve().is_relative_to(base_path)


def allowed_file(filename):
    """
    Checks if a file has a permitted extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_mime_type(file_path):
    """
    Detects the MIME type of a file.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def save_file(upload_folder, file):
    """
    Securely saves an uploaded file.
    """
    if not allowed_file(file.filename):
        logger.error(f"File type not allowed: {file.filename}")
        return None, "File type not allowed"

    filename = secure_filename(file.filename)
    file_path = Path(upload_folder) / filename

    if not is_safe_path(SAFE_STORAGE_PATH, file_path):
        logger.error(f"Unsafe file path detected: {file_path}")
        return None, "Invalid file path"

    file.save(file_path)
    logger.info(f"File saved successfully: {file_path}")
    return str(file_path), None


def read_file(file_path):
    """
    Securely reads a file.
    """
    file_path = Path(file_path).resolve()

    if not is_safe_path(SAFE_STORAGE_PATH, file_path):
        logger.error(f"Unauthorized file access attempt: {file_path}")
        return None, "Unauthorized access"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None, "File not found"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content, None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None, str(e)


def write_file(file_path, data):
    """
    Securely writes data to a file.
    """
    file_path = Path(file_path).resolve()

    if not is_safe_path(SAFE_STORAGE_PATH, file_path):
        logger.error(f"Unauthorized write attempt: {file_path}")
        return False, "Unauthorized write attempt"

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(data)
        logger.info(f"Data written to file: {file_path}")
        return True, None
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False, str(e)


def delete_file(file_path):
    """
    Deletes a file securely.
    """
    file_path = Path(file_path).resolve()

    if not is_safe_path(SAFE_STORAGE_PATH, file_path):
        logger.error(f"Unauthorized delete attempt: {file_path}")
        return False, "Unauthorized delete attempt"

    if not file_path.exists():
        logger.warning(f"File already deleted or missing: {file_path}")
        return False, "File not found"

    try:
        file_path.unlink()
        logger.info(f"File deleted: {file_path}")
        return True, None
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False, str(e)


def move_file(source, destination):
    """
    Moves a file to a new location securely.
    """
    source = Path(source).resolve()
    destination = Path(destination).resolve()

    if not is_safe_path(SAFE_STORAGE_PATH, source) or not is_safe_path(SAFE_STORAGE_PATH, destination):
        logger.error(f"Unauthorized move attempt: {source} -> {destination}")
        return False, "Unauthorized move attempt"

    try:
        shutil.move(str(source), str(destination))
        logger.info(f"File moved: {source} -> {destination}")
        return True, None
    except Exception as e:
        logger.error(f"Error moving file {source} -> {destination}: {e}")
        return False, str(e)


def calculate_md5(file_path):
    """
    Computes MD5 hash of a file for integrity verification.
    """
    file_path = Path(file_path).resolve()

    if not is_safe_path(SAFE_STORAGE_PATH, file_path):
        logger.error(f"Unauthorized access for MD5 hash: {file_path}")
        return None, "Unauthorized access"

    if not file_path.exists():
        logger.error(f"File not found for hashing: {file_path}")
        return None, "File not found"

    try:
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest(), None
    except Exception as e:
        logger.error(f"Error calculating MD5 for {file_path}: {e}")
        return None, str(e)
