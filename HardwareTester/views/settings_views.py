from flask import Blueprint, request, jsonify
from HardwareTester.services.settings_service import SettingsService
from HardwareTester.extensions import logger

settings_bp = Blueprint("settings", __name__)

# ----------------------
# Global Settings Endpoints
# ----------------------

@settings_bp.route("/settings/global/<key>", methods=["GET"])
def get_global_setting_view(key):
    """Retrieve a global setting by key."""
    logger.info(f"Fetching global setting for key: {key}")
    try:
        value = SettingsService.get_global_setting(key)
        if value is None:
            logger.warning(f"Global setting '{key}' not found.")
            return jsonify({"success": False, "message": "Setting not found."}), 404
        logger.info(f"Global setting '{key}' retrieved successfully.")
        return jsonify({"success": True, "key": key, "value": value})
    except Exception as e:
        logger.error(f"Error retrieving global setting '{key}': {e}")
        return jsonify({"success": False, "message": "Error retrieving global setting."}), 500


@settings_bp.route("/settings/global", methods=["POST"])
def update_global_setting_view():
    """Update or create a global setting."""
    logger.info("Updating global setting.")
    try:
        data = request.json
        key = data.get("key")
        value = data.get("value")
        if not key or value is None:
            logger.warning("Missing 'key' or 'value' in global settings update request.")
            return jsonify({"success": False, "message": "Key and value are required."}), 400
        result = SettingsService.update_global_setting(key, value)
        if result["success"]:
            logger.info(f"Global setting '{key}' updated successfully.")
        else:
            logger.warning(f"Failed to update global setting '{key}'.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating global setting: {e}")
        return jsonify({"success": False, "message": "Error updating global setting."}), 500


@settings_bp.route("/settings/global", methods=["GET"])
def list_global_settings_view():
    """List all global settings."""
    logger.info("Fetching all global settings.")
    try:
        settings = SettingsService.list_global_settings()
        logger.info(f"Retrieved {len(settings)} global settings.")
        return jsonify({"success": True, "settings": settings})
    except Exception as e:
        logger.error(f"Error listing global settings: {e}")
        return jsonify({"success": False, "message": "Error retrieving global settings."}), 500


# ----------------------
# User Settings Endpoints
# ----------------------

@settings_bp.route("/settings/user/<int:user_id>", methods=["GET"])
def get_user_settings_view(user_id):
    """Retrieve user-specific settings."""
    logger.info(f"Fetching settings for user ID: {user_id}")
    try:
        settings = SettingsService.get_user_settings(user_id)
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
    try:
        data = request.json
        if not data:
            logger.warning(f"Update request for user ID {user_id} missing data.")
            return jsonify({"success": False, "message": "Request data is required."}), 400
        result = SettingsService.update_user_settings(user_id, data)
        if result["success"]:
            logger.info(f"Settings for user ID {user_id} updated successfully.")
        else:
            logger.warning(f"Failed to update settings for user ID {user_id}.")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating settings for user ID {user_id}: {e}")
        return jsonify({"success": False, "message": "Error updating settings."}), 500
