
from flask import Blueprint, render_template, jsonify
from HardwareTester.services.reports_service import generate_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
def reports():
    """Render reports page."""
    return render_template("reports.html")

@reports_bp.route("/generate", methods=["POST"])
def generate_report_view():
    """Generate a report."""
    report_data = generate_report()
    return jsonify(report_data)

