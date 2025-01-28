
from flask import Blueprint, jsonify, request
from flask_login import login_required
from HardwareTester.services.source_code_analyzer import SourceCodeAnalyzer

source_bp = Blueprint("source", __name__, url_prefix="/source")

@source_bp.route("/analyze", methods=["POST"])
@login_required
def analyze_source():
    """
    API endpoint to analyze source code and return class/method metadata.
    """
    try:
        repo_path = request.json.get("repo_path")
        if not repo_path:
            return jsonify({"success": False, "message": "Repository path is required."}), 400

        analyzer = SourceCodeAnalyzer()
        results = analyzer.analyze_repo(repo_path)

        return jsonify({"success": True, "methods": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error analyzing source: {e}"}), 500
