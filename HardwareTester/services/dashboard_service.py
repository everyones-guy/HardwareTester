from HardwareTester.models import db, DashboardData, User, Role, Metric
from HardwareTester.utils.logger import Logger
from sqlalchemy.exc import SQLAlchemyError

logger = Logger(name="DashboardService", log_file="logs/dashboard_service.log", level="INFO")


class DashboardService:
    @staticmethod
    def get_dashboard_data(user_id):
        """Fetch dashboard data for a specific user.
           :param user_id: ID of the user
           :return: JSON response with the data
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"success": False, "error": "User not found"}

            if user.role != Role.query.filter_by(name='admin').first():
                return {"success": False, "error": "Access denied"}

            data = DashboardData.query.filter_by(user_id=user_id).all()
            return {"success": True, "data": [d.to_dict() for d in data]}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching dashboard data: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error fetching dashboard data: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_aggregated_metrics():
        """Fetch aggregated metrics for the dashboard.
           :return: JSON response with aggregated metrics
        """
        try:
            total_users = User.query.count()
            total_devices = Metric.query.filter_by(metric_type="device_count").count()
            total_notifications = DashboardData.query.filter_by(type="notification").count()

            aggregated_data = {
                "total_users": total_users,
                "total_devices": total_devices,
                "total_notifications": total_notifications
            }
            return {"success": True, "metrics": aggregated_data}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching aggregated metrics: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error fetching aggregated metrics: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_dashboard_item(user_id, title, description, type="custom"):
        """Create a new dashboard item."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {"success": False, "error": "User not found"}

            new_item = DashboardData(user_id=user_id, title=title, description=description, type=type)
            db.session.add(new_item)
            db.session.commit()
            logger.info(f"Dashboard item '{title}' created for user {user_id}")
            return {"success": True, "message": "Dashboard item created successfully"}
        except SQLAlchemyError as e:
            logger.error(f"Database error creating dashboard item: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error creating dashboard item: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_dashboard_item(item_id, title=None, description=None):
        """Update an existing dashboard item."""
        try:
            item = DashboardData.query.get(item_id)
            if not item:
                return {"success": False, "error": "Dashboard item not found"}

            if title:
                item.title = title
            if description:
                item.description = description

            db.session.commit()
            logger.info(f"Dashboard item {item_id} updated")
            return {"success": True, "message": "Dashboard item updated successfully"}
        except SQLAlchemyError as e:
            logger.error(f"Database error updating dashboard item: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error updating dashboard item: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_dashboard_item(item_id):
        """Delete a dashboard item."""
        try:
            item = DashboardData.query.get(item_id)
            if not item:
                return {"success": False, "error": "Dashboard item not found"}

            db.session.delete(item)
            db.session.commit()
            logger.info(f"Dashboard item {item_id} deleted")
            return {"success": True, "message": "Dashboard item deleted successfully"}
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting dashboard item: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error deleting dashboard item: {e}")
            return {"success": False, "error": str(e)}
