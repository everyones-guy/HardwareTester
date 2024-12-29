
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from HardwareTester.services.dashboard_service import DashboardService

# Create the Blueprint
main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"])
def index():
    """
    Render the index/home page.
    """
    return render_template("index.html")

@main_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """
    Render the dashboard page with dynamic data.
    """
    dashboard_data = DashboardService.get_dashboard_data(current_user.id)
    return render_template("dashboard.html", data=dashboard_data)

@main_bp.route("/about", methods=["GET"])
def about():
    """
    Render the About Us page.
    """
    return render_template("about.html")

@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """
    Handle the contact form.
    """
    if request.method == "POST":
        # Process the contact form submission
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Save or send the contact message (e.g., via email or database)
        # Example response
        response = {"success": True, "message": "Thank you for contacting us!"}

        return jsonify(response)
    return render_template("contact.html")

@main_bp.route("/error", methods=["GET"])
def error_page():
    """
    Render a generic error page.
    """
    return render_template("error.html")

