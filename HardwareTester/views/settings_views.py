from flask import Blueprint, request, jsonify
from HardwareTester.services.settings_service import (
    get_global_setting,
    update_global_setting,
    list_global_settings,
    get_user_settings,
    update_user_settings,
)
from HardwareTester.extensions import logger

settings_bp = Blueprint("settings", __name__)

# ----------------------
# Global Settings Endpoints
# ----------------------

@settings_bp.route("/settings/global/<key>", methods=["GET"])
def get_global_setting_view(key):
    """Retrieve a global setting by key."""
    logger.info(f"Fetching global setting for key: {key}")
    value = get_global_setting(key)
    if value is None:
        logger.warning(f"Global setting '{key}' not found.")
        return jsonify({"success": False, "message": "Setting not found."}), 404
    logger.info(f"Global setting '{key}' retrieved successfully.")
    return jsonify({"success": True, "key": key, "value": value})


@settings_bp.route("/settings/global", methods=["POST"])
def update_global_setting_view():
    """Update or create a global setting."""
    data = request.json
    key = data.get("key")
    value = data.get("value")
    if not key or value is None:
        logger.warning("Missing 'key' or 'value' in global settings update request.")
        return jsonify({"success": False, "message": "Key and value are required."}), 400
    result = update_global_setting(key, value)
    if result["success"]:
        logger.info(f"Global setting '{key}' updated successfully.")
    else:
        logger.error(f"Failed to update global setting '{key}'.")
    return jsonify(result)


@settings_bp.route("/settings/global", methods=["GET"])
def list_global_settings_view():
    """List all global settings."""
    logger.info("Fetching all global settings.")
    settings = list_global_settings()
    logger.info(f"Retrieved {len(settings)} global settings.")
    return jsonify({"success": True, "settings": settings})


# ----------------------
# User Settings Endpoints
# ----------------------

@settings_bp.route("/settings/user/<int:user_id>", methods=["GET"])
def get_user_settings_view(user_id):
    """Retrieve user-specific settings."""
    logger.info(f"Fetching settings for user ID: {user_id}")
    try:
        settings = get_user_settings(user_id)
        if not settings:
            logger.warning(f"No settings found for user ID: {user_id}")
            return jsonify({"success": False, "message": "No settings found for the user."}), 404
        logger.info(f"Settings for user ID {user_id} retrieved successfully.")
        return jsonify({"success": True, "settings": settings})
    except Exception as e:
        logger.error(f"Error fetching settings for user ID {user_id}: {e}")
        return jsonify({"success": False, "message": "Error retrieving settings."}), 500


@settings_bp.route("/settings/user/<int:user_id>", methods=["POST"])
def update_user_settings_view(user_id):
    """Update user-specific settings."""
    logger.info(f"Updating settings for user ID: {user_id}")
    data = request.json
    if not data:
        logger.warning(f"Update request for user ID {user_id} missing data.")
        return jsonify({"success": False, "message": "Request data is required."}), 400
    try:
        result = update_user_settings(user_id, data)
        if result["success"]:
            logger.info(f"Settings for user ID {user_id} updated successfully.")
        else:
            logger.warning(f"Failed to update settings for user ID {user_id}.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating settings for user ID {user_id}: {e}")
        return jsonify({"success": False, "message": "Error updating settings."}), 500
