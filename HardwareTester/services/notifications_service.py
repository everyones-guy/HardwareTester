# notifications_service.py
# This file contains the NotificationService class, which provides methods for managing user notifications.

from datetime import datetime
from HardwareTester.extensions import db, logger
from HardwareTester.models.log_models import Notification
from sqlalchemy.exc import SQLAlchemyError

class NotificationService:
    """Service for managing user notifications."""

    @staticmethod
    def fetch_notifications(user_id: int) -> dict:
        """
        Fetch notifications for a specific user.
        :param user_id: ID of the user.
        :return: Dictionary containing notifications or an error message.
        """
        try:
            notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()
            result = [
                {
                    "id": n.id,
                    "message": n.message,
                    "type": n.notification_type,
                    "read": n.read,
                    "timestamp": n.timestamp.isoformat(),
                }
                for n in notifications
            ]
            logger.info(f"Fetched {len(result)} notifications for user {user_id}.")
            return {"success": True, "notifications": result}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching notifications for user {user_id}: {e}")
            return {"success": False, "error": "Failed to fetch notifications."}
        except Exception as e:
            logger.error(f"Unexpected error fetching notifications for user {user_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def mark_as_read(notification_id: int) -> dict:
        """
        Mark a specific notification as read.
        :param notification_id: ID of the notification.
        :return: Success or error message.
        """
        try:
            notification = Notification.query.get(notification_id)
            if not notification:
                logger.warning(f"Notification ID {notification_id} not found.")
                return {"success": False, "error": "Notification not found."}

            notification.read = True
            db.session.commit()
            logger.info(f"Notification ID {notification_id} marked as read.")
            return {"success": True, "message": "Notification marked as read."}
        except SQLAlchemyError as e:
            logger.error(f"Database error marking notification {notification_id} as read: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to mark notification as read."}
        except Exception as e:
            logger.error(f"Unexpected error marking notification {notification_id} as read: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def create_notification(user_id: int, message: str, notification_type: str = "info") -> dict:
        """
        Create a new notification for a user.
        :param user_id: ID of the user.
        :param message: Content of the notification.
        :param notification_type: Type of notification (info, warning, error).
        :return: Success or error message.
        """
        try:
            new_notification = Notification(
                user_id=user_id,
                message=message,
                notification_type=notification_type,
                timestamp=datetime.utcnow(),
                read=False,
            )
            db.session.add(new_notification)
            db.session.commit()
            logger.info(f"Notification created for user {user_id}: {message}")
            return {"success": True, "message": "Notification created successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error creating notification for user {user_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to create notification."}
        except Exception as e:
            logger.error(f"Unexpected error creating notification for user {user_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def delete_notification(notification_id: int) -> dict:
        """
        Delete a specific notification.
        :param notification_id: ID of the notification.
        :return: Success or error message.
        """
        try:
            notification = Notification.query.get(notification_id)
            if not notification:
                logger.warning(f"Notification ID {notification_id} not found.")
                return {"success": False, "error": "Notification not found."}

            db.session.delete(notification)
            db.session.commit()
            logger.info(f"Notification ID {notification_id} deleted.")
            return {"success": True, "message": "Notification deleted successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting notification {notification_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to delete notification."}
        except Exception as e:
            logger.error(f"Unexpected error deleting notification {notification_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def clear_all_notifications(user_id: int) -> dict:
        """
        Clear all notifications for a specific user.
        :param user_id: ID of the user.
        :return: Success or error message.
        """
        try:
            notifications = Notification.query.filter_by(user_id=user_id).all()
            for notification in notifications:
                db.session.delete(notification)

            db.session.commit()
            logger.info(f"Cleared all notifications for user {user_id}.")
            return {"success": True, "message": "All notifications cleared successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error clearing notifications for user {user_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to clear notifications."}
        except Exception as e:
            logger.error(f"Unexpected error clearing notifications for user {user_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def list_notifications() -> dict:
        """
        Retrieve all notifications.
        :return: Dictionary containing all notifications or an error message.
        """
        try:
            notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
            result = [
                {
                    "id": n.id,
                    "message": n.message,
                    "type": n.notification_type,
                    "read": n.read,
                    "timestamp": n.timestamp.isoformat(),
                }
                for n in notifications
            ]
            logger.info(f"Retrieved {len(result)} notifications.")
            return {"success": True, "notifications": result}
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving notifications: {e}")
            return {"success": False, "error": "Failed to retrieve notifications."}
        except Exception as e:
            logger.error(f"Unexpected error retrieving notifications: {e}")
            return {"success": False, "error": "An unexpected error occurred."}
