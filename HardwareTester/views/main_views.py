from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"], endpoint="dashboard")
def dashboard():
    """Render the Dashboard."""
    return render_template("dashboard.html")

@main_bp.route("/about", methods=["GET"], endpoint="about")
def about():
    """Render the About page."""
    return render_template("about.html")
