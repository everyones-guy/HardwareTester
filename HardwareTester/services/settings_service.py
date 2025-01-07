# settings_service.py

import os
from HardwareTester.extensions import db, logger
from HardwareTester.models import UserSettings, GlobalSettings
from sqlalchemy.exc import SQLAlchemyError

class SettingsService:
    """Service for managing user and global settings."""

    # ----------------------
    # Global Settings Methods
    # ----------------------

    @staticmethod
    def get_global_setting(key: str) -> dict:
        """
        Retrieve a global setting by key.
        :param key: The key of the global setting.
        :return: The value of the global setting or an error message.
        """
        try:
            setting = GlobalSettings.query.filter_by(key=key).first()
            if not setting:
                logger.warning(f"Global setting '{key}' not found.")
                return {"success": False, "error": "Setting not found."}
            logger.info(f"Retrieved global setting '{key}': {setting.value}.")
            return {"success": True, "value": setting.value}
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving global setting '{key}': {e}")
            return {"success": False, "error": "Failed to retrieve setting."}

    @staticmethod
    def update_global_setting(key: str, value: str) -> dict:
        """
        Update or create a global setting.
        :param key: The key of the global setting.
        :param value: The value to set.
        :return: Success or error message.
        """
        try:
            setting = GlobalSettings.query.filter_by(key=key).first()
            if not setting:
                setting = GlobalSettings(key=key, value=value)
                db.session.add(setting)
            else:
                setting.value = value
            db.session.commit()
            logger.info(f"Global setting '{key}' updated to '{value}'.")
            return {"success": True, "message": f"Setting '{key}' updated successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error updating global setting '{key}': {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to update setting."}

    @staticmethod
    def list_global_settings() -> dict:
        """
        List all global settings.
        :return: A list of global settings or an error message.
        """
        try:
            settings = GlobalSettings.query.all()
            result = [
                {"key": setting.key, "value": setting.value, "updated_at": setting.updated_at.isoformat()}
                for setting in settings
            ]
            logger.info(f"Retrieved {len(result)} global settings.")
            return {"success": True, "settings": result}
        except SQLAlchemyError as e:
            logger.error(f"Database error listing global settings: {e}")
            return {"success": False, "error": "Failed to list settings."}

    # ----------------------
    # User Settings Methods
    # ----------------------

    @staticmethod
    def get_user_settings(user_id: int) -> dict:
        """
        Retrieve user-specific settings.
        :param user_id: The ID of the user.
        :return: User settings or an error message.
        """
        try:
            settings = UserSettings.query.filter_by(user_id=user_id).first()
            if not settings:
                logger.warning(f"No settings found for user {user_id}.")
                return {"success": False, "error": "No settings found for user."}
            logger.info(f"Retrieved settings for user {user_id}.")
            return {"success": True, "settings": settings.settings}
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving settings for user {user_id}: {e}")
            return {"success": False, "error": "Failed to retrieve settings."}

    @staticmethod
    def update_user_settings(user_id: int, new_settings: dict) -> dict:
        """
        Update user-specific settings.
        :param user_id: The ID of the user.
        :param new_settings: The new settings to apply.
        :return: Success or error message.
        """
        try:
            settings = UserSettings.query.filter_by(user_id=user_id).first()
            if not settings:
                settings = UserSettings(user_id=user_id, settings=new_settings)
                db.session.add(settings)
            else:
                settings.settings.update(new_settings)
            db.session.commit()
            logger.info(f"Updated settings for user {user_id}.")
            return {"success": True, "message": "User settings updated successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error updating settings for user {user_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to update settings."}

    @staticmethod
    def reset_user_settings(user_id: int) -> dict:
        """
        Reset user settings to defaults.
        :param user_id: The ID of the user.
        :return: Success or error message.
        """
        try:
            settings = UserSettings.query.filter_by(user_id=user_id).first()
            if not settings:
                logger.warning(f"No settings found for user {user_id} to reset.")
                return {"success": False, "error": "No settings found to reset."}

            # Reset to default values
            settings.settings = {}
            db.session.commit()
            logger.info(f"Settings reset to defaults for user {user_id}.")
            return {"success": True, "message": "Settings reset to defaults."}
        except SQLAlchemyError as e:
            logger.error(f"Database error resetting settings for user {user_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to reset settings."}

    @staticmethod
    def list_user_settings() -> dict:
        """
        List all user-specific settings.
        :return: A list of user settings or an error message.
        """
        try:
            settings = UserSettings.query.all()
            result = [
                {"user_id": setting.user_id, "settings": setting.settings} for setting in settings
            ]
            logger.info(f"Retrieved settings for {len(result)} users.")
            return {"success": True, "user_settings": result}
        except SQLAlchemyError as e:
            logger.error(f"Database error listing user settings: {e}")
            return {"success": False, "error": "Failed to list settings."}
