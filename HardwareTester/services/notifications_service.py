
# notifications_service.py

from HardwareTester.utils.logger import Logger
from HardwareTester.models import db, Notification
from datetime import datetime

logger = Logger(name="NotificationService", log_file="logs/notification_service.log", level="INFO")

def fetch_notifications(user_id):
    """
    Fetch notifications for a specific user.
    :param user_id: ID of the user.
    :return: List of notifications or an error message.
    """
    try:
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()
        result = [
            {
                "id": notification.id,
                "message": notification.message,
                "type": notification.notification_type,
                "read": notification.read,
                "timestamp": notification.timestamp.isoformat(),
            }
            for notification in notifications
        ]
        logger.info(f"Fetched {len(result)} notifications for user {user_id}.")
        return {"success": True, "notifications": result}
    except Exception as e:
        logger.error(f"Failed to fetch notifications for user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def mark_as_read(notification_id):
    """
    Mark a specific notification as read.
    :param notification_id: ID of the notification.
    :return: Success or error message.
    """
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            logger.error(f"Notification ID {notification_id} not found.")
            return {"success": False, "error": "Notification not found."}
        
        notification.read = True
        db.session.commit()
        logger.info(f"Notification ID {notification_id} marked as read.")
        return {"success": True, "message": "Notification marked as read."}
    except Exception as e:
        logger.error(f"Failed to mark notification {notification_id} as read: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}

def create_notification(user_id, message, notification_type="info"):
    """
    Create a new notification for a user.
    :param user_id: ID of the user.
    :param message: Message content of the notification.
    :param notification_type: Type of notification (info, warning, error).
    :return: Success or error message.
    """
    try:
        new_notification = Notification(
            user_id=user_id,
            message=message,
            notification_type=notification_type,
            timestamp=datetime.datetime.utcnow(),
            read=False,
        )
        db.session.add(new_notification)
        db.session.commit()
        logger.info(f"Notification created for user {user_id}: {message}")
        return {"success": True, "message": "Notification created successfully."}
    except Exception as e:
        logger.error(f"Failed to create notification for user {user_id}: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}

def delete_notification(notification_id):
    """
    Delete a specific notification.
    :param notification_id: ID of the notification.
    :return: Success or error message.
    """
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            logger.error(f"Notification ID {notification_id} not found.")
            return {"success": False, "error": "Notification not found."}
        
        db.session.delete(notification)
        db.session.commit()
        logger.info(f"Notification ID {notification_id} deleted.")
        return {"success": True, "message": "Notification deleted successfully."}
    except Exception as e:
        logger.error(f"Failed to delete notification {notification_id}: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}

def clear_all_notifications(user_id):
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
    except Exception as e:
        logger.error(f"Failed to clear notifications for user {user_id}: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}









def list_notifications():
    """Retrieve all notifications."""
    try:
        notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
        notification_list = [
            {"id": n.id, "title": n.title, "message": n.message, "type": n.type, "timestamp": n.timestamp.isoformat()}
            for n in notifications
        ]
        logger.info("Retrieved notifications successfully.")
        return {"success": True, "notifications": notification_list}
    except Exception as e:
        logger.error(f"Error retrieving notifications: {e}")
        return {"success": False, "error": str(e)}


def add_notification(title, message, notification_type="info"):
    """Add a new notification."""
    try:
        new_notification = Notification(
            title=title, message=message, type=notification_type, timestamp=datetime.utcnow()
        )
        db.session.add(new_notification)
        db.session.commit()
        logger.info(f"Notification '{title}' added successfully.")
        return {"success": True, "message": "Notification added successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding notification '{title}': {e}")
        return {"success": False, "error": str(e)}


def delete_notification(notification_id):
    """Delete a specific notification."""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return {"success": False, "error": "Notification not found."}
        
        db.session.delete(notification)
        db.session.commit()
        logger.info(f"Notification ID '{notification_id}' deleted successfully.")
        return {"success": True, "message": f"Notification ID '{notification_id}' deleted successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting notification ID '{notification_id}': {e}")
        return {"success": False, "error": str(e)}


