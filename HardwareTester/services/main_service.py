# main_service.py uses the Logger class from logger.py to log messages. The Logger class is a wrapper around the Python logging module. It provides methods for logging messages at different levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) and allows for dynamic adjustment of the log level. The logger is initialized with a log file and log level, and log messages are written to both the log file and the console.

from datetime import datetime
from HardwareTester.models.user_models import User, ContactMessage, DashboardData
from HardwareTester.utils.db_utils import db_session
from sqlalchemy.exc import SQLAlchemyError
from HardwareTester.extensions import logger
import os

class MainService:
    @staticmethod
    def fetch_main_dashboard_data(user_id: int) -> dict:
        """
        Fetch and return data for the user's dashboard.
        
        :param user_id: ID of the current user.
        :return: Dictionary containing dashboard data.
        """
        try:
            with db_session() as session:
                dashboard_data = session.query(DashboardData).filter_by(user_id=user_id).all()
                data = [
                    {
                        "title": item.title,
                        "description": item.description,
                        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for item in dashboard_data
                ]
                logger.info(f"Fetched dashboard data for user {user_id}.")
                return {"success": True, "data": data}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching dashboard data for user {user_id}: {e}")
            return {"success": False, "error": "Failed to fetch dashboard data."}
        except Exception as e:
            logger.error(f"Unexpected error fetching dashboard data for user {user_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def save_contact_message(name: str, email: str, message: str) -> dict:
        """
        Save a contact message to the database.

        :param name: Name of the person.
        :param email: Email of the person.
        :param message: Message content.
        :return: Dictionary with the operation result.
        """
        try:
            with db_session() as session:
                contact_message = ContactMessage(
                    name=name,
                    email=email,
                    message=message,
                    submitted_at=datetime.utcnow(),
                )
                session.add(contact_message)
                session.commit()
                logger.info(f"Contact message from {email} saved successfully.")
                return {"success": True, "message": "Thank you for contacting us!"}
        except SQLAlchemyError as e:
            logger.error(f"Database error saving contact message from {email}: {e}")
            return {"success": False, "error": "Failed to save contact message."}
        except Exception as e:
            logger.error(f"Unexpected error saving contact message from {email}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def fetch_error_logs(log_file: str = "logs/app_error.log") -> dict:
        """
        Fetch and return application error logs.

        :param log_file: Path to the log file.
        :return: List of error logs.
        """
        try:
            if not os.path.exists(log_file):
                logger.warning(f"Log file {log_file} not found.")
                return {"success": False, "error": "Log file not found."}

            with open(log_file, "r") as file:
                logs = file.readlines()
                logger.info(f"Fetched error logs from {log_file}.")
                return {"success": True, "logs": logs}
        except Exception as e:
            logger.error(f"Error fetching logs from {log_file}: {e}")
            return {"success": False, "error": "An unexpected error occurred while fetching logs."}
