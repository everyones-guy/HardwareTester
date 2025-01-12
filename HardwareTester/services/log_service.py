from datetime import datetime
from HardwareTester.models.log_models import ActivityLog, Notification
from HardwareTester.extensions import db, logger
from HardwareTester.utils.centralized_logger import CentralizedLogger


class LogService:
    """A service for managing logs."""

    @staticmethod
    def log_activity(user_id, action):
        """Log an activity into the database."""
        try:
            activity = ActivityLog(user_id=user_id, action=action)
            db.session.add(activity)
            db.session.commit()
            CentralizedLogger.log_info(f"Activity logged: {action} for User {user_id}")
            return {"success": True, "message": "Activity logged successfully."}
        except Exception as e:
            CentralizedLogger.log_error(f"Error logging activity for User {user_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to log activity: {str(e)}"}

    @staticmethod
    def get_activity_logs(user_id=None, start_date=None, end_date=None):
        """Retrieve activity logs with optional filters."""
        try:
            query = ActivityLog.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            if start_date:
                query = query.filter(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.filter(ActivityLog.timestamp <= end_date)

            logs = query.order_by(ActivityLog.timestamp.desc()).all()
            CentralizedLogger.log_info(f"Fetched {len(logs)} activity logs.")
            return {"success": True, "logs": [log.__repr__() for log in logs]}
        except Exception as e:
            CentralizedLogger.log_error(f"Error fetching activity logs: {e}")
            return {"success": False, "error": f"Failed to fetch logs: {str(e)}"}

    @staticmethod
    def send_notification(message, user_id=None):
        """Send a notification to a user or all users."""
        try:
            notification = Notification(message=message, user_id=user_id)
            db.session.add(notification)
            db.session.commit()
            recipient = f"User {user_id}" if user_id else "All Users"
            CentralizedLogger.log_info(f"Notification sent: {message} to {recipient}")
            return {"success": True, "message": f"Notification sent to {recipient}."}
        except Exception as e:
            CentralizedLogger.log_error(f"Error sending notification: {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to send notification: {str(e)}"}

    @staticmethod
    def get_notifications(user_id=None, only_unread=False):
        """Retrieve notifications with optional filters."""
        try:
            query = Notification.query
            if user_id:
                query = query.filter_by(user_id=user_id)
            if only_unread:
                query = query.filter_by(is_read=False)

            notifications = query.order_by(Notification.id.desc()).all()
            CentralizedLogger.log_info(f"Fetched {len(notifications)} notifications.")
            return {"success": True, "notifications": [n.__repr__() for n in notifications]}
        except Exception as e:
            CentralizedLogger.log_error(f"Error fetching notifications: {e}")
            return {"success": False, "error": f"Failed to fetch notifications: {str(e)}"}

    @staticmethod
    def mark_notification_as_read(notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.query.get(notification_id)
            if not notification:
                return {"success": False, "error": "Notification not found."}

            notification.is_read = True
            db.session.commit()
            CentralizedLogger.log_info(f"Marked notification {notification_id} as read.")
            return {"success": True, "message": "Notification marked as read."}
        except Exception as e:
            CentralizedLogger.log_error(f"Error marking notification {notification_id} as read: {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to mark notification as read: {str(e)}"}
