from flask_bcrypt import Bcrypt
import logging

# Initialize bcrypt
bcrypt = Bcrypt()

# Configure logging for password utilities
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bcrypt_utils")

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
        raise ValueError("Failed to hash the password. Please try again.")

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
        raise ValueError("Invalid password hash format.")
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        raise ValueError("An unexpected error occurred during password verification.")

def is_strong_password(password: str) -> bool:
    """
    Check if a password meets basic security criteria.
    :param password: The plaintext password to validate.
    :return: True if the password is strong, False otherwise.
    """
    if len(password) < 8:
        logger.warning("Password is too short. Minimum length is 8 characters.")
        return False
    if not any(char.isdigit() for char in password):
        logger.warning("Password must include at least one digit.")
        return False
    if not any(char.isupper() for char in password):
        logger.warning("Password must include at least one uppercase letter.")
        return False
    if not any(char.islower() for char in password):
        logger.warning("Password must include at least one lowercase letter.")
        return False
    if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/`~" for char in password):
        logger.warning("Password must include at least one special character.")
        return False
    logger.info("Password meets strength requirements.")
    return True
