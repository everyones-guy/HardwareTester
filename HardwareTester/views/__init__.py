from flask import Blueprint
from HardwareTester.views.main_views import main_bp
from HardwareTester.views.auth_views import auth_bp
from HardwareTester.views.configuration_views import configuration_bp
from HardwareTester.views.dashboard_views import dashboard_bp
from HardwareTester.views.emulator_views import emulator_bp
from HardwareTester.views.log_views import logs_bp
from HardwareTester.views.hardware_views import hardware_bp
from HardwareTester.views.mqtt_views import mqtt_bp
from HardwareTester.views.peripherals_views import peripherals_bp
from HardwareTester.views.reports_views import reports_bp
from HardwareTester.views.settings_views import settings_bp
from HardwareTester.views.system_status_views import system_status_bp
from HardwareTester.views.test_plan_views import test_plan_bp
from HardwareTester.views.user_management_views import user_management_bp
from HardwareTester.views.notifications_views import notifications_bp
from HardwareTester.views.upload_views import upload_bp
from HardwareTester.views.api_views import api_bp
from HardwareTester.views.valve_views import valve_bp
from HardwareTester.views.source_routes import source_bp
from HardwareTester.views.source_code_routes import source_code_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(configuration_bp, url_prefix="/configurations")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(emulator_bp, url_prefix="/emulators")
    app.register_blueprint(logs_bp, url_prefix="/logs")
    app.register_blueprint(hardware_bp, url_prefix="/hardware")
    app.register_blueprint(mqtt_bp, url_prefix="/mqtt")
    app.register_blueprint(peripherals_bp, url_prefix="/peripherals")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(system_status_bp, url_prefix="/system-status")
    app.register_blueprint(test_plan_bp, url_prefix="/test-plans")
    app.register_blueprint(user_management_bp, url_prefix="/users")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(upload_bp, url_prefix="/upload")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(valve_bp, url_prefix="/valves")
    app.register_blueprint(source_code_bp, url_prefix="/api/source-code")
