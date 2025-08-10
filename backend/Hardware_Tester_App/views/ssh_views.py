from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from Hardware_Tester_App.services.ssh_service import SSHService
from Hardware_Tester_App.extensions import db, logger
#from Hardware_Tester_App.utils.custom_logger import CustomLogger

# Initialize logger
#logger = CustomLogger.get_logger("ssh_views")

ssh_bp = Blueprint("ssh", __name__)


@ssh_bp.route("/api/ssh", methods=["GET"])
@login_required
def ssh_dashboard():
    """Render the SSH management dashboard."""
    try:
        return render_template("ssh_dashboard.html")
    except Exception as e:
        logger.error(f"Error rendering SSH dashboard: {e}")
        return jsonify({"success": False, "error": "Failed to render the SSH dashboard."}), 500


@ssh_bp.route("/api/ssh/connections", methods=["GET"])
@login_required
def list_connections():
    """List all saved SSH connections."""
    try:
        connections = db.SSHConnection.query.all()
        connection_list = [
            {
                "id": conn.id,
                "name": conn.name,
                "host": conn.host,
                "port": conn.port,
                "username": conn.username,
            }
            for conn in connections
        ]
        return jsonify({"success": True, "connections": connection_list})
    except Exception as e:
        logger.error(f"Error listing SSH connections: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ssh_bp.route("/api/ssh/connection/<int:connection_id>", methods=["GET"])
@login_required
def get_connection(connection_id):
    """Retrieve a specific SSH connection."""
    try:
        connection = db.SSHConnection.query.get(connection_id)
        if not connection:
            return jsonify({"success": False, "error": "SSH connection not found"}), 404

        return jsonify(
            {
                "success": True,
                "connection": {
                    "id": connection.id,
                    "name": connection.name,
                    "host": connection.host,
                    "port": connection.port,
                    "username": connection.username,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving SSH connection {connection_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ssh_bp.route("/api/ssh/connection", methods=["POST"])
@login_required
def save_connection():
    """Save a new SSH connection."""
    data = request.json
    name = data.get("name")
    host = data.get("host")
    port = data.get("port", 22)
    username = data.get("username")
    password = data.get("password")

    if not all([name, host, username, password]):
        return jsonify({"success": False, "error": "All fields are required"}), 400

    try:
        connection = db.SSHConnection(
            name=name, host=host, port=port, username=username, password=password
        )
        db.session.add(connection)
        db.session.commit()

        logger.info(f"Saved SSH connection: {name}")
        return jsonify({"success": True, "message": "SSH connection saved successfully."})
    except Exception as e:
        logger.error(f"Error saving SSH connection: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@ssh_bp.route("/api/ssh/connection/<int:connection_id>", methods=["DELETE"])
@login_required
def delete_connection(connection_id):
    """Delete an SSH connection."""
    try:
        connection = db.SSHConnection.query.get(connection_id)
        if not connection:
            return jsonify({"success": False, "error": "SSH connection not found"}), 404

        db.session.delete(connection)
        db.session.commit()

        logger.info(f"Deleted SSH connection: {connection.name}")
        return jsonify({"success": True, "message": "SSH connection deleted successfully."})
    except Exception as e:
        logger.error(f"Error deleting SSH connection {connection_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ssh_bp.route("/api/ssh/test", methods=["POST"])
@login_required
def test_connection():
    """Test an SSH connection."""
    data = request.json
    host = data.get("host")
    port = data.get("port", 22)
    username = data.get("username")
    password = data.get("password")

    if not all([host, username, password]):
        return jsonify({"success": False, "error": "Host, username, and password are required"}), 400

    try:
        ssh_service = SSHService(device_id="test", host=host, port=port)
        connected = ssh_service.connect(username=username, password=password)

        if connected:
            ssh_service.disconnect()
            return jsonify({"success": True, "message": "SSH connection test successful."})
        else:
            return jsonify({"success": False, "error": "SSH connection test failed."}), 500
    except Exception as e:
        logger.error(f"Error testing SSH connection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ssh_bp.route("/api/ssh/setup-wizard", methods=["GET", "POST"])
@login_required
def ssh_setup_wizard():
    """Setup wizard for creating and testing SSH connections."""
    if request.method == "GET":
        try:
            return render_template("ssh_setup_wizard.html")
        except Exception as e:
            logger.error(f"Error rendering SSH setup wizard: {e}")
            return jsonify({"success": False, "error": "Failed to render the SSH setup wizard."}), 500

    elif request.method == "POST":
        data = request.json
        name = data.get("name")
        host = data.get("host")
        port = data.get("port", 22)
        username = data.get("username")
        password = data.get("password")

        if not all([name, host, username, password]):
            return jsonify({"success": False, "error": "All fields are required"}), 400

        try:
            # Test the connection before saving
            ssh_service = SSHService(device_id="test", host=host, port=port)
            connected = ssh_service.connect(username=username, password=password)

            if connected:
                ssh_service.disconnect()

                # Save the connection if the test is successful
                connection = db.SSHConnection(
                    name=name, host=host, port=port, username=username, password=password
                )
                db.session.add(connection)
                db.session.commit()

                return jsonify({"success": True, "message": "SSH connection tested and saved successfully."})
            else:
                return jsonify({"success": False, "error": "SSH connection test failed."}), 500
        except Exception as e:
            logger.error(f"Error during SSH setup wizard: {e}")
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

