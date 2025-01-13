from HardwareTester.extensions import bcrypt
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize bcrypt and logger
logger = CustomLogger.get_logger("bcrypt_utils")

def hash_password(password: str) -> str:
    """
    Generate a hashed password using bcrypt.
    :param password: The plaintext password to hash.
    :return: The hashed password as a UTF-8 string.
    """
    try:
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        logger.info("Password successfully hashed.")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise RuntimeError("Failed to hash the password. Please try again.")

def check_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    :param password: The plaintext password to verify.
    :param hashed_password: The hashed password to compare against.
    :return: True if the password matches the hash, False otherwise.
    """
    try:
        is_valid = bcrypt.check_password_hash(hashed_password, password)
        if is_valid:
            logger.info("Password verification successful.")
        else:
            logger.warning("Password verification failed.")
        return is_valid
    except ValueError as e:
        logger.error(f"Invalid hash provided: {e}")
        raise ValueError("Invalid password hash format.") from e
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        raise RuntimeError("An unexpected error occurred during password verification.") from e
    
def is_strong_password(password: str) -> bool:
    """
    Check if a password meets basic security criteria.
    :param password: The plaintext password to validate.
    :return: True if the password is strong, False otherwise.
    """
    criteria = {
        "length": len(password) >= 8,
        "digit": any(char.isdigit() for char in password),
        "uppercase": any(char.isupper() for char in password),
        "lowercase": any(char.islower() for char in password),
        "special": any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/`~" for char in password),
    }

    failed_criteria = [key for key, passed in criteria.items() if not passed]
    if failed_criteria:
        logger.debug(f"Password failed strength criteria: {failed_criteria}")
        return False

    logger.info("Password meets strength requirements.")
    return True
