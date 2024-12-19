from flask import Blueprint

# Import individual blueprints
from HardwareTester.views.main_views import main_bp
from HardwareTester.views.valve_views import valve_bp
from HardwareTester.views.test_plan_views import test_plan_bp
from HardwareTester.views.log_views import log_bp
from HardwareTester.views.api_views import api_bp
from HardwareTester.views.serial_views import serial_bp
from HardwareTester.views.configuration_views import configuration_bp
from HardwareTester.views.error_views import error_bp
from HardwareTester.views.mqtt_views import mqtt_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(valve_bp, url_prefix="/valves")
    app.register_blueprint(test_plan_bp, url_prefix="/test-plans")
    app.register_blueprint(log_bp, url_prefix="/logs")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(serial_bp, url_prefix="/serial")
    app.register_blueprint(configuration_bp, url_prefix="/configurations")
    
    
