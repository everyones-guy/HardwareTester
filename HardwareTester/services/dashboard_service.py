import logging
from HardwareTester.models.user_models import User, Role  # Update imports based on your models
from HardwareTester.models.dashboard_models import DashboardData
from HardwareTester.extensions import db
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logger = logging.getLogger("DashboardService")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/dashboard_service.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class DashboardService:
    @staticmethod
    def get_dashboard_data(user_id: int) -> dict:
        """
        Fetch dashboard data for a specific user.
        :param user_id: ID of the user
        :return: JSON response with the data
        """
        try:
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return {"success": False, "error": "User not found"}

            # Check if user is an admin
            admin_role = Role.query.filter_by(name="admin").first()
            if not admin_role or user.role_id != admin_role.id:
                logger.warning(f"Access denied for user {user_id}")
                return {"success": False, "error": "Access denied"}

            # Fetch dashboard data
            data = db.DashboardData.query.filter_by(user_id=user_id).all()
            logger.info(f"Fetched dashboard data for user {user_id}")
            return {"success": True, "data": [d.to_dict() for d in data]}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching dashboard data for user {user_id}: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error fetching dashboard data for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_aggregated_metrics() -> dict:
        """
        Fetch aggregated metrics for the dashboard.
        :return: JSON response with aggregated metrics
        """
        try:
            total_users = db.User.query.count()
            total_devices = db.Metric.query.filter_by(metric_type="device_count").count()
            total_notifications = db.DashboardData.query.filter_by(type="notification").count()

            aggregated_data = {
                "total_users": total_users,
                "total_devices": total_devices,
                "total_notifications": total_notifications,
            }
            logger.info("Aggregated metrics fetched successfully")
            return {"success": True, "metrics": aggregated_data}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching aggregated metrics: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error fetching aggregated metrics: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_dashboard_item(user_id: int, title: str, description: str, type: str = "custom") -> dict:
        """
        Create a new dashboard item.
        :param user_id: ID of the user
        :param title: Title of the dashboard item
        :param description: Description of the dashboard item
        :param type: Type of the dashboard item (default: "custom")
        :return: JSON response
        """
        try:
            user = db.User.query.get(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return {"success": False, "error": "User not found"}

            new_item = db.DashboardData(user_id=user_id, title=title, description=description, type=type)
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
    def update_dashboard_item(item_id: int, title: str = None, description: str = None) -> dict:
        """
        Update an existing dashboard item.
        :param item_id: ID of the dashboard item
        :param title: New title (optional)
        :param description: New description (optional)
        :return: JSON response
        """
        try:
            item = DashboardData.query.get(item_id)
            if not item:
                logger.warning(f"Dashboard item {item_id} not found")
                return {"success": False, "error": "Dashboard item not found"}

            if title:
                item.title = title
            if description:
                item.description = description

            db.session.commit()
            logger.info(f"Dashboard item {item_id} updated")
            return {"success": True, "message": "Dashboard item updated successfully"}
        except SQLAlchemyError as e:
            logger.error(f"Database error updating dashboard item {item_id}: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error updating dashboard item {item_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_dashboard_item(item_id: int) -> dict:
        """
        Delete a dashboard item.
        :param item_id: ID of the dashboard item
        :return: JSON response
        """
        try:
            item = DashboardData.query.get(item_id)
            if not item:
                logger.warning(f"Dashboard item {item_id} not found")
                return {"success": False, "error": "Dashboard item not found"}

            db.session.delete(item)
            db.session.commit()
            logger.info(f"Dashboard item {item_id} deleted")
            return {"success": True, "message": "Dashboard item deleted successfully"}
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting dashboard item {item_id}: {e}")
            return {"success": False, "error": "Database error"}
        except Exception as e:
            logger.error(f"Unexpected error deleting dashboard item {item_id}: {e}")
            return {"success": False, "error": str(e)}
