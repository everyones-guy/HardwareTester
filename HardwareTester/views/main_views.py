from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from HardwareTester.services.dashboard_service import DashboardService
from HardwareTester.extensions import logger
from datetime import datetime
#from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
#logger = CustomLogger.get_logger("main_views")

# Create the Blueprint
main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
@login_required
def index():
    """
    Render the index/home page.
    """
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Error rendering the index page: {e}")
        return redirect(url_for("main.error_page"))


@main_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """
    Render the dashboard page with dynamic data.
    """
    try:
        # Fetch dashboard data for the logged-in user
        dashboard_data = DashboardService.get_dashboard_data(user_id=current_user.id)
        if dashboard_data["success"]:
            return render_template("dashboard.html", data=dashboard_data["data"])
        else:
            logger.error(f"Error fetching dashboard data: {dashboard_data['error']}")
            flash("Failed to load dashboard data.", "danger")
            return redirect(url_for("main.error_page"))
    except Exception as e:
        logger.error(f"Error rendering the dashboard page: {e}")
        return redirect(url_for("main.error_page"))


@main_bp.route("/about", methods=["GET"])
@login_required
def about():
    """
    Render the About Us page.
    """
    try:
        return render_template("about.html")
    except Exception as e:
        logger.error(f"Error rendering the About Us page: {e}")
        return redirect(url_for("main.error_page"))


@main_bp.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    """
    Handle the contact form.
    """
    try:
        if request.method == "POST":
            # Process the contact form submission
            name = request.form.get("name")
            email = request.form.get("email")
            message = request.form.get("message")

            if not name or not email or not message:
                flash("All fields are required.", "danger")
                return redirect(url_for("main.contact"))

            # Placeholder for actual implementation
            logger.info(f"Contact form submitted by {name}, {email}")
            flash("Thank you for contacting us!", "success")
            return redirect(url_for("main.contact"))

        return render_template("contact.html")
    except Exception as e:
        logger.error(f"Error handling the contact form: {e}")
        flash("An unexpected error occurred. Please try again later.", "danger")
        return redirect(url_for("main.error_page"))


@main_bp.route("/terms", methods=["GET"])
@login_required
def terms():
    """
    Render the Terms of Service page.
    """
    try:
        return render_template("terms.html")
    except Exception as e:
        logger.error(f"Error rendering the Terms of Service page: {e}")
        return redirect(url_for("main.error_page"))


@main_bp.route("/privacy", methods=["GET"])
@login_required
def privacy():
    """
    Render the Privacy Policy page.
    """
    try:
        return render_template("privacy.html")
    except Exception as e:
        logger.error(f"Error rendering the Privacy Policy page: {e}")
        return redirect(url_for("main.error_page"))


@main_bp.route("/error", methods=["GET"])
@login_required
def error_page():
    """
    Render a generic error page.
    """
    return render_template("error.html")


@main_bp.route("/search", methods=["GET"])
@login_required
def search():
    """
    Search functionality for the application.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "Search query cannot be empty."}), 400

    try:
        # Placeholder for actual search implementation
        logger.info(f"Search query received: {query}")
        results = {"example_result": f"Results for {query}"}
        return jsonify({"success": True, "results": results})
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


# Additional helper routes (optional)

@main_bp.route("/health", methods=["GET"])
@login_required
def health_check():
    """
    Health check endpoint to confirm the application is running.
    """
    return jsonify({"success": True, "message": "Application is healthy."})
