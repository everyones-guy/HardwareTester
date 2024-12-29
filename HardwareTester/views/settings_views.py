
from flask import Blueprint, request, jsonify
from HardwareTester.services.settings_service import (
    get_global_setting,
    update_global_setting,
    list_global_settings,
    get_user_settings,
    update_user_settings,
)

settings_bp = Blueprint("settings", __name__)

# ----------------------
# Global Settings Endpoints
# ----------------------

@settings_bp.route("/settings/global/<key>", methods=["GET"])
def get_global_setting_view(key):
    """Retrieve a global setting by key."""
    value = get_global_setting(key)
    if value is None:
        return jsonify({"success": False, "message": "Setting not found."}), 404
    return jsonify({"success": True, "key": key, "value": value})

@settings_bp.route("/settings/global", methods=["POST"])
def update_global_setting_view():
    """Update or create a global setting."""
    data = request.json
    key = data.get("key")
    value = data.get("value")
    if not key or value is None:
        return jsonify({"success": False, "message": "Key and value are required."}), 400
    result = update_global_setting(key, value)
    return jsonify(result)

@settings_bp.route("/settings/global", methods=["GET"])
def list_global_settings_view():
    """List all global settings."""
    settings = list_global_settings()
    return jsonify({"success": True, "settings": settings})

# ----------------------
# User Settings Endpoints
# ----------------------

@settings_bp.route("/settings/user/<int:user_id>", methods=["GET"])
def get_user_settings_view(user_id):
    """Retrieve user-specific settings."""
    settings = get_user_settings(user_id)
    return jsonify({"success": True, "settings": settings})

@settings_bp.route("/settings/user/<int:user_id>", methods=["POST"])
def update_user_settings_view(user_id):
    """Update user-specific settings."""
    data = request.json
    result = update_user_settings(user_id, data)
    return jsonify(result)

