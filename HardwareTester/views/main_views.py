from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from HardwareTester.services.dashboard_service import DashboardService
from datetime import datetime
from HardwareTester.extensions import logger

# Create the Blueprint
main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"])
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
        dashboard_data = DashboardService.get_dashboard_data(current_user.id)
        return render_template("dashboard.html", data=dashboard_data)
    except Exception as e:
        logger.error(f"Error rendering the dashboard page: {e}")
        return redirect(url_for("main.error_page"))

@main_bp.route("/about", methods=["GET"])
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
                return jsonify({"success": False, "error": "All fields are required."}), 400

            # Save or send the contact message (e.g., via email or database)
            # Placeholder for actual implementation
            logger.info(f"Contact form submitted: {name}, {email}")
            response = {"success": True, "message": "Thank you for contacting us!"}
            return jsonify(response)

        return render_template("contact.html")
    except Exception as e:
        logger.error(f"Error handling the contact form: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@main_bp.route("/terms", methods=["GET"])
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
def error_page():
    """
    Render a generic error page.
    """
    return render_template("error.html")


@main_bp.route("/search", methods=["GET"])
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

