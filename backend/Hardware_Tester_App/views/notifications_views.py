
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from Hardware_Tester_App.services.notifications_service import NotificationService

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/notifications", methods=["GET"])
@login_required
def notifications_page():
    """Render the notifications page."""
    return render_template("notifications.html")


@notifications_bp.route("/api/notifications/list", methods=["GET"])
@login_required
def list_notifications_endpoint():
    """Retrieve all notifications."""
    response = NotificationService.list_notifications()
    return jsonify(response)


@notifications_bp.route("/api/notifications/add", methods=["POST"])
@login_required
def add_notification_endpoint():
    """Add a new notification."""
    data = request.json
    response = NotificationService.add_notification(data["title"], data["message"], data.get("type", "info"))
    return jsonify(response)


@notifications_bp.route("/api/notifications/delete/<int:notification_id>", methods=["DELETE"])
@login_required
def delete_notification_endpoint(notification_id):
    """Delete a notification."""
    response = NotificationService.delete_notification(notification_id)
    return jsonify(response)

