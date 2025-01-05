from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def hash_password(password: str) -> str:
    """Generate a hashed password."""
    return bcrypt.generate_password_hash(password).decode("utf-8")

def check_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.check_password_hash(hashed_password, password)

