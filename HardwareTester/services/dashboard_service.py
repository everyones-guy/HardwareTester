
from HardwareTester.models import db, DashboardData, User
from HardwareTester.utils.logger import Logger

logger = Logger(name="DashboardService", log_file="logs/dashboard_service.log", level="INFO")


class DashboardService:
    @staticmethod
    def get_dashboard_data(user_id):
        """Fetch dashboard data for a specific user.
           :param user_id: Id of the user
           :return: JSON response with the data
        """
        try:
            data = DashboardData.query.filter_by(user_id=user_id).all()
            return {"success": True, "data": [d.to_dict() for d in data]}
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def create_dashboard_item(user_id, title, description):
        """Create a new dashboard item."""
        try:
            new_item = DashboardData(user_id=user_id, title=title, description=description)
            db.session.add(new_item)
            db.session.commit()
            logger.info(f"Dashboard item '{title}' created for user {user_id}")
            return {"success": True, "message": "Dashboard item created successfully"}
        except Exception as e:
            logger.error(f"Error creating dashboard item: {e}")
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
        except Exception as e:
            logger.error(f"Error updating dashboard item: {e}")
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
        except Exception as e:
            logger.error(f"Error deleting dashboard item: {e}")
            return {"success": False, "error": str(e)}

