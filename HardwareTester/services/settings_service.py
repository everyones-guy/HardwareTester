
# settings_service.py
import os
from HardwareTester.utils.logger import Logger
from HardwareTester.models import UserSettings, GlobalSettings, db

logger = Logger(name="SettingsService", log_file="logs/settings_service.log", level="INFO")

def list_all_settings():
    """
    List all user settings for administrative purposes.
    :return: List of settings or an error message.
    """
    try:
        settings_list = UserSettings.query.all()
        result = [
            {
                "id": settings.id,
                "user_id": settings.user_id,
                "preferences": settings.preferences,
                "notifications": settings.notifications,
                "theme": settings.theme,
            }
            for settings in settings_list
        ]
        logger.info(f"Retrieved settings for {len(result)} users.")
        return {"success": True, "settings": result}
    except Exception as e:
        logger.error(f"Failed to list all user settings: {e}")
        return {"success": False, "error": str(e)}

def get_application_settings():
    """
    Retrieve global application settings.
    :return: Dictionary of application settings or an error message.
    """
    try:
        app_settings = {
            "max_upload_size": os.getenv("MAX_CONTENT_LENGTH", "16MB"),
            "allowed_file_types": {
                "spec_sheets": os.getenv("ALLOWED_SPEC_SHEET_EXTENSIONS", "").split(","),
                "test_plans": os.getenv("ALLOWED_TEST_PLAN_EXTENSIONS", "").split(","),
            },
            "mqtt_settings": {
                "broker": os.getenv("MQTT_BROKER", "test.mosquitto.org"),
                "port": os.getenv("MQTT_PORT", 1883),
                "tls": os.getenv("MQTT_TLS", "False") == "True",
            },
        }
        logger.info("Retrieved application settings.")
        return {"success": True, "app_settings": app_settings}
    except Exception as e:
        logger.error(f"Failed to retrieve application settings: {e}")
        return {"success": False, "error": str(e)}

    # ----------------------
# Global Settings Methods
# ----------------------

def get_global_setting(key):
    """Retrieve a global setting by key."""
    return GlobalSettings.get_setting(key)

def update_global_setting(key, value):
    """Update or create a global setting."""
    GlobalSettings.update_setting(key, value)
    return {"success": True, "message": f"Global setting '{key}' updated."}

def list_global_settings():
    """List all global settings."""
    settings = GlobalSettings.query.all()
    return [
        {"key": setting.key, "value": setting.value, "updated_at": setting.updated_at}
        for setting in settings
    ]

# ----------------------
# User Settings Methods
# ----------------------
def get_user_settings(user_id):
    """Retrieve user-specific settings."""
    user_settings = UserSettings.query.filter_by(user_id=user_id).first()
    return user_settings.settings if user_settings else {}

def update_user_settings(user_id, new_settings):
    """Update user-specific settings."""
    user_settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=user_id, settings=new_settings)
        db.session.add(user_settings)
    else:
        user_settings.update_settings(new_settings)
    db.session.commit()
    return {"success": True, "message": "User settings updated successfully."}

def list_user_settings():
    """List all user-specific settings."""
    users_with_settings = UserSettings.query.all()
    return [
        {"user_id": user_setting.user_id, "settings": user_setting.settings}
        for user_setting in users_with_settings
    ]
def reset_user_settings(user_id):
    """
    Reset user settings to defaults.
    :param user_id: ID of the user.
    :return: Success or error message.
    """
    try:
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            logger.warning(f"No settings found for user {user_id} to reset.")
            return {"success": False, "error": "No settings found to reset."}

        # Reset to default values
        settings.preferences = {}
        settings.notifications = {}
        settings.theme = "default"
        db.session.commit()
        logger.info(f"Settings reset to defaults for user {user_id}.")
        return {"success": True, "message": "Settings reset to defaults."}
    except Exception as e:
        logger.error(f"Failed to reset settings for user {user_id}: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e)}
		

