
# user_management.py

from werkzeug.security import generate_password_hash, check_password_hash
from HardwareTester.utils.bcrypt_utils import hash_password, check_password, is_strong_password
from HardwareTester.extensions import db, logger
from HardwareTester.models.user_models import User
from sqlalchemy.exc import SQLAlchemyError

class UserManagementService:
    """Service for managing user accounts."""

    @staticmethod
    def create_user(username: str, email: str, password: str) -> dict:
        """
        Create a new user.
        :param username: Unique username.
        :param email: User's email address.
        :param password: User's password.
        :return: Success or error message.
        """
        logger.info(f"Creating user '{username}'...")
        try:
            if User.query.filter((User.username == username) | (User.email == email)).first():
                logger.warning("Username or email already exists.")
                return {"success": False, "error": "Username or email already exists."}
            
            #Using built in methods from bcrypt_utils.py
            #if the password is strong, hash it otherwise return an error

            if is_strong_password(password):
                hashed_password = hash_password(password)
            else:
                return {"success": False, "error": "Password is not strong enough."}
            
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"User '{username}' created successfully.")
            return {"success": True, "message": f"User '{username}' created successfully."}
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error creating user '{username}': {e}")
            return {"success": False, "error": "Failed to create user."}
        except Exception as e:
            logger.error(f"Unexpected error creating user '{username}': {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_user(user_id: int) -> dict:
        """
        Retrieve a user's information.
        :param user_id: ID of the user.
        :return: User details or error message.
        """
        logger.info(f"Fetching user ID {user_id}...")
        try:
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"User ID {user_id} not found.")
                return {"success": False, "error": "User not found."}

            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            logger.info(f"User ID {user_id} retrieved successfully.")
            return {"success": True, "user": user_data}
        except Exception as e:
            logger.error(f"Error fetching user ID {user_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_users() -> dict:
        """
        Retrieve a list of all users.
        :return: List of users or error message.
        """
        logger.info("Fetching list of users...")
        try:
            users = User.query.all()
            user_list = [
                {"id": user.id, "username": user.username, "email": user.email, "created_at": user.created_at}
                for user in users
            ]
            logger.info(f"Retrieved {len(user_list)} users successfully.")
            return {"success": True, "users": user_list}
        except Exception as e:
            logger.error(f"Error retrieving user list: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def authenticate_user(username: str, password: str) -> dict:
        """
        Authenticate a user by username and password.
        :param username: Username of the user.
        :param password: Password of the user.
        :return: Authentication result and user info if successful.
        """
        logger.info(f"Authenticating user '{username}'...")
        try:
            user = User.query.filter_by(username=username).first()
            if not user or not check_password(user.password, password):
                logger.warning(f"Authentication failed for user '{username}'.")
                return {"success": False, "error": "Invalid username or password."}

            logger.info(f"User '{username}' authenticated successfully.")
            return {"success": True, "user": {"id": user.id, "username": user.username, "email": user.email}}
        except Exception as e:
            logger.error(f"Error authenticating user '{username}': {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_user(user_id: int, username: str = None, email: str = None, password: str = None) -> dict:
        """
        Update user details.
        :param user_id: ID of the user.
        :param username: New username (optional).
        :param email: New email (optional).
        :param password: New password (optional).
        :return: Success or error message.
        """
        logger.info(f"Updating user ID {user_id}...")
        try:
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"User ID {user_id} not found.")
                return {"success": False, "error": "User not found."}

            if username:
                user.username = username
            if email:
                user.email = email
            if password:
                user.password = hash_password(password)

            db.session.commit()
            logger.info(f"User ID {user_id} updated successfully.")
            return {"success": True, "message": f"User ID {user_id} updated successfully."}
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error updating user ID {user_id}: {e}")
            return {"success": False, "error": "Failed to update user."}
        except Exception as e:
            logger.error(f"Unexpected error updating user ID {user_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_user(user_id: int) -> dict:
        """
        Delete a user.
        :param user_id: ID of the user to delete.
        :return: Success or error message.
        """
        logger.info(f"Deleting user ID {user_id}...")
        try:
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"User ID {user_id} not found.")
                return {"success": False, "error": "User not found."}

            db.session.delete(user)
            db.session.commit()
            logger.info(f"User ID {user_id} deleted successfully.")
            return {"success": True, "message": f"User ID {user_id} deleted successfully."}
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error deleting user ID {user_id}: {e}")
            return {"success": False, "error": "Failed to delete user."}
        except Exception as e:
            logger.error(f"Unexpected error deleting user ID {user_id}: {e}")
            return {"success": False, "error": str(e)}