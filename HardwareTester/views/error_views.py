from flask import Blueprint, render_template

error_bp = Blueprint("error", __name__)

@error_bp.app_errorhandler(404)
def not_found_error(error):
    """Render the 404 error page."""
    return render_template("error.html", message="Resource not found!"), 404

@error_bp.app_errorhandler(500)
def internal_server_error(error):
    """Render the 500 error page."""
    return render_template("error.html", message="An internal server error occurred!"), 500
