from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from Hardware_Tester_App.extensions import db
from Hardware_Tester_App.models import Valve, TestPlan
from Hardware_Tester_App.utils.parsers import parse_test_plan, parse_spec_sheet
from Hardware_Tester_App.utils.validators import validate_file_upload
import os

# Blueprint for main views
main = Blueprint("main", __name__)

# Route: Dashboard
@main.route("/")
def dashboard():
    """Render the main dashboard."""
    return render_template("dashboard.html")

# Route: Valve Management
@main.route("/valve-management")
def valve_management():
    """Render the valve management page."""
    valves = Valve.query.all()
    return render_template("valve_management.html", valves=valves)

# Route: Upload Spec Sheet
@main.route("/upload-spec-sheet", methods=["GET", "POST"])
def upload_spec_sheet():
    """Handle uploading spec sheets."""
    if request.method == "POST":
        file = request.files.get("file")
        valve_id = request.form.get("valve_id")

        # Validate the uploaded file
        is_valid, message = validate_file_upload(file, {"pdf", "docx", "xlsx"}, 16)
        if not is_valid:
            flash(message, "danger")
            return redirect(url_for("main.upload_spec_sheet"))

        # Save the file
        filename = os.path.join("uploads", "spec_sheets", file.filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        file.save(filename)

        # Optionally associate with a valve
        if valve_id:
            valve = Valve.query.get(valve_id)
            if valve:
                valve.specifications = {"spec_sheet": filename}
                db.session.commit()
                flash(f"Spec sheet uploaded and associated with valve {valve.name}.", "success")
            else:
                flash("Valve ID not found.", "danger")
        else:
            flash("Spec sheet uploaded successfully.", "success")

        return redirect(url_for("main.upload_spec_sheet"))

    return render_template("upload_spec_sheet.html")

# Route: Upload Test Plan
@main.route("/upload-test-plan", methods=["GET", "POST"])
def upload_test_plan():
    """Handle uploading test plans."""
    if request.method == "POST":
        file = request.files.get("file")

        # Validate the uploaded file
        is_valid, message = validate_file_upload(file, {"pdf", "csv", "txt"}, 16)
        if not is_valid:
            flash(message, "danger")
            return redirect(url_for("main.upload_test_plan"))

        # Parse and save the test plan
        try:
            steps = parse_test_plan(file)
            test_plan = TestPlan(name=file.filename, uploaded_by="Admin", steps=steps)
            db.session.add(test_plan)
            db.session.commit()
            flash("Test plan uploaded successfully.", "success")
        except Exception as e:
            flash(f"Error parsing test plan: {str(e)}", "danger")

        return redirect(url_for("main.upload_test_plan"))

    return render_template("upload_test_plan.html")

# Route: Run Test Plan
@main.route("/run-test-plan/<int:test_plan_id>", methods=["POST"])
def run_test_plan(test_plan_id):
    """Run a specific test plan."""
    test_plan = TestPlan.query.get(test_plan_id)
    if not test_plan:
        return jsonify({"success": False, "message": "Test plan not found."})

    # Simulate running the test plan (replace with actual logic)
    results = [{"step": step, "result": "Success"} for step in test_plan.steps]

    return jsonify({"success": True, "results": results})

# Route: View System Info
@main.route("/get-system-info", methods=["GET"])
def get_system_info():
    """Fetch and display system information."""
    from Hardware_Tester_App.utils.hardware_manager import get_system_info
    info = get_system_info()
    return jsonify({"success": True, "info": info})
