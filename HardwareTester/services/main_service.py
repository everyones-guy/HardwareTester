
# main_service.py

import logging
from datetime import datetime

# Assuming database models are available
from HardwareTester.models import User, ContactMessage, DashboardData
from HardwareTester.utils.db_utils import db_session
from HardwareTester.services.dashboard_service import get_dashboard_data

# Set up logging
logger = logging.getLogger("MainService")
logger.setLevel(logging.INFO)

# Define the Main Service
class MainService:
    @staticmethod
    def fetch_main_dashboard_data(user_id):
        """
        Fetch and return data for the dashboard.
        
        :param user_id: ID of the current user.
        :return: Dictionary containing dashboard data.
        """
        #return get_dashboard_data(user_id)
        try:
            with db_session() as session:
                # Example query to fetch user-specific dashboard data
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
        except Exception as e:
            logger.error(f"Error fetching dashboard data for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def save_contact_message(name, email, message):
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
        except Exception as e:
            logger.error(f"Error saving contact message from {email}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def fetch_error_logs():
        """
        Fetch and return application error logs.

        :return: List of error logs.
        """
        try:
            # Assuming logs are stored in a file
            with open("logs/app_error.log", "r") as log_file:
                logs = log_file.readlines()
                logger.info("Fetched error logs.")
                return {"success": True, "logs": logs}
        except FileNotFoundError:
            logger.warning("Error log file not found.")
            return {"success": False, "error": "Error log file not found."}
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            return {"success": False, "error": str(e)}


