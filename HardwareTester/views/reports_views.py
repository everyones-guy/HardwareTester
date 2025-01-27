
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from HardwareTester.services.reports_service import generate_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
@login_required
def reports():
    """Render reports page."""
    return render_template("reports.html")

@reports_bp.route("/generate", methods=["POST"])
@login_required
def generate_report_view():
    """Generate a report."""
    report_data = generate_report()
    return jsonify(report_data)

