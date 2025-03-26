
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from Hardware_Tester_App.services.reports_service import generate_report

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports")
@login_required
def reports():
    """Render reports page."""
    return render_template("reports.html")

@reports_bp.route("/api/reports/generate", methods=["POST"])
@login_required
def generate_report_view():
    """Generate a report."""
    report_data = generate_report()
    return jsonify(report_data)

