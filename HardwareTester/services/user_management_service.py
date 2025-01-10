
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
        try:
            if User.query.filter((User.username == username) | (User.email == email)).first():
                return {"success": False, "error": "Username or email already exists."}
            if is_strong_password(password):
                hashed_password = hash_password(password)
            else:
                return {"success": False, "error": "Password is not strong enough."}

            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return {"success": True, "message": f"User '{username}' created successfully."}
        except SQLAlchemyError:
            db.session.rollback()
            return {"success": False, "error": "Failed to create user."}

    @staticmethod
    def list_users(page: int = 1, per_page: int = 10) -> dict:
        try:
            paginated_users = User.query.paginate(page=page, per_page=per_page, error_out=False)
            user_list = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at,
                }
                for user in paginated_users.items
            ]
            return {"success": True, "users": user_list, "total": paginated_users.total}
        except Exception as e:
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