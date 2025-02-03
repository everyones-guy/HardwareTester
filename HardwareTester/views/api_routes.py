from flask import Blueprint
from HardwareTester.views.api_views import (
    api_overview,
    get_configuration_by_blueprint,
    test_connection,
    fetch_data,
    push_data,
    get_available_endpoints,
    get_overview,
    get_device_config,
    simulate_device,
    create_test_plan,
    emulator_save_json,
)

# Blueprint for API operations
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Define routes
api_bp.route("/", methods=["GET"])(api_overview)
api_bp.route("/configurations/<string:blueprint>", methods=["GET"])(get_configuration_by_blueprint)
api_bp.route("/test-connection", methods=["GET"])(test_connection)
api_bp.route("/fetch-data", methods=["POST"])(fetch_data)
api_bp.route("/push-data", methods=["POST"])(push_data)
api_bp.route("/endpoints", methods=["GET"])(get_available_endpoints)
api_bp.route("/get-overview", methods=["GET"])(get_overview)
api_bp.route("/device-config", methods=["GET"])(get_device_config)
api_bp.route("/simulate-device", methods=["POST"])(simulate_device)
api_bp.route("/test-plans", methods=["POST"])(create_test_plan)
api_bp.route("/emulators/json/save", methods=["POST"])(emulator_save_json)
