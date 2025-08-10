# validators.py
# This module contains utility functions for validating user input.
import os
import re


def validate_email(email):
    """
    Validate an email address format.
    :param email: The email address to validate.
    :return: (bool, str) Tuple where the first value indicates success and the second is a message.
    """
    if not email:
        return False, "Email address cannot be empty."

    # Define a regex pattern for validating an email address
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    if not re.match(email_regex, email):
        return False, "Invalid email address format."
    
    return True, "Email address is valid."


def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension.
    :param filename: Name of the file to check.
    :param allowed_extensions: Set of allowed file extensions.
    :return: True if the file extension is allowed, False otherwise.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def validate_file_upload(file, allowed_extensions, max_size_mb):
    """
    Validate an uploaded file's extension and size.
    :param file: File object to validate.
    :param allowed_extensions: Set of allowed file extensions.
    :param max_size_mb: Maximum file size in megabytes.
    :return: (bool, str) Tuple where the first value indicates success and the second is a message.
    """
    if not file:
        return False, "No file uploaded."
    
    # Check filename
    if file.filename == "":
        return False, "File name cannot be empty."

    if not allowed_file(file.filename, allowed_extensions):
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}."
    
    # Check file size
    file.seek(0, os.SEEK_END)  # Move the cursor to the end of the file to get its size
    file_size_mb = file.tell() / (1024 * 1024)  # Convert bytes to MB
    file.seek(0)  # Reset the file pointer to the beginning

    if file_size_mb > max_size_mb:
        return False, f"File size exceeds the {max_size_mb} MB limit."
    
    return True, "File is valid."


def validate_test_plan_steps(steps):
    """
    Validate the structure of a test plan's steps.
    :param steps: List of steps to validate.
    :return: (bool, str) Tuple where the first value indicates success and the second is a message.
    """
    if not isinstance(steps, list):
        return False, "Test plan steps must be a list."
    
    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            return False, f"Step {i} must be a dictionary."
        if "Step" not in step or "Action" not in step or "Parameter" not in step:
            return False, f"Step {i} is missing required keys ('Step', 'Action', 'Parameter')."
        if not isinstance(step["Step"], int):
            return False, f"'Step' in step {i} must be an integer."
        if not isinstance(step["Action"], str) or not step["Action"].strip():
            return False, f"'Action' in step {i} must be a non-empty string."
        if not isinstance(step["Parameter"], (str, int, float)):
            return False, f"'Parameter' in step {i} must be a string, integer, or float."
    
    return True, "Test plan steps are valid."


def validate_valve_id(valve_id):
    """
    Validate a valve ID.
    :param valve_id: Valve ID to validate.
    :return: (bool, str) Tuple where the first value indicates success and the second is a message.
    """
    if not valve_id:
        return False, "Valve ID cannot be empty."
    
    if not isinstance(valve_id, int) or valve_id <= 0:
        return False, "Valve ID must be a positive integer."
    
    return True, "Valve ID is valid."


def validate_json(data, required_keys):
    """
    Validate that a JSON object contains required keys.
    :param data: JSON object to validate.
    :param required_keys: List of keys that must be present in the JSON object.
    :return: (bool, str) Tuple where the first value indicates success and the second is a message.
    """
    if not isinstance(data, dict):
        return False, "Input data must be a JSON object (dictionary)."
    
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return False, f"Missing required keys: {', '.join(missing_keys)}."
    
    return True, "JSON object is valid."

