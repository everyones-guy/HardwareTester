
# user_management.py

from werkzeug.security import generate_password_hash, check_password_hash
from HardwareTester.models import db, User
from HardwareTester.utils.logger import Logger

logger = Logger(name="UserManagementService", log_file="logs/user_management_service.log", level="INFO")

def create_user(username, email, password):
    """
    Create a new user.
    :param username: Unique username.
    :param email: User's email address.
    :param password: User's password.
    :return: Success or error message.
    """
    try:
        if User.query.filter((User.username == username) | (User.email == email)).first():
            logger.error("Username or email already exists.")
            return {"success": False, "error": "Username or email already exists."}

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User {username} created successfully.")
        return {"success": True, "message": f"User {username} created successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {e}")
        return {"success": False, "error": str(e)}

def get_user(user_id):
    """
    Retrieve a user's information.
    :param user_id: ID of the user.
    :return: User details or error message.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error("User not found.")
            return {"success": False, "error": "User not found."}

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
        logger.info(f"Retrieved user {user_id} successfully.")
        return {"success": True, "user": user_data}
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        return {"success": False, "error": str(e)}


def list_users():
    """
    Retrieve a list of all users.
    :return: List of users or error message.
    """
    try:
        users = User.query.all()
        user_list = [
            {"id": user.id, "username": user.username, "email": user.email, "created_at": user.created_at}
            for user in users
        ]
        logger.info("Retrieved list of users successfully.")
        return {"success": True, "users": user_list}
    except Exception as e:
        logger.error(f"Error retrieving user list: {e}")
        return {"success": False, "error": str(e)}


def authenticate_user(username, password):
    """
    Authenticate a user by username and password.
    :param username: Username of the user.
    :param password: Password of the user.
    :return: Authentication result and user info if successful.
    """
    try:
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            logger.warning(f"Authentication failed for user {username}.")
            return {"success": False, "error": "Invalid username or password."}

        logger.info(f"User {username} authenticated successfully.")
        return {"success": True, "user": {"id": user.id, "username": user.username, "email": user.email}}
    except Exception as e:
        logger.error(f"Error authenticating user {username}: {e}")
        return {"success": False, "error": str(e)}

def add_user(username, email, password):
    """Add a new user."""
    try:
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User '{username}' added successfully.")
        return {"success": True, "message": f"User '{username}' added successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding user '{username}': {e}")
        return {"success": False, "error": str(e)}


def update_user(user_id, username=None, email=None, password=None):
    """Update user details."""
    try:
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
        
        if username:
            user.username = username
        if email:
            user.email = email
        if password:
            user.password = generate_password_hash(password)
        
        db.session.commit()
        logger.info(f"User ID '{user_id}' updated successfully.")
        return {"success": True, "message": f"User ID '{user_id}' updated successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user ID '{user_id}': {e}")
        return {"success": False, "error": str(e)}


def delete_user(user_id):
    """Delete a user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
        
        db.session.delete(user)
        db.session.commit()
        logger.info(f"User ID '{user_id}' deleted successfully.")
        return {"success": True, "message": f"User ID '{user_id}' deleted successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user ID '{user_id}': {e}")
        return {"success": False, "error": str(e)}

