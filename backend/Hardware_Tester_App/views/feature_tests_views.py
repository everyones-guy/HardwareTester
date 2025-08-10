
from flask import Blueprint, jsonify
from flask_login import login_required
import subprocess

feature_tests_bp = Blueprint('feature_tests', __name__)

@feature_tests_bp.route('/run-feature-tests', methods=['POST'])
@login_required
def run_feature_tests():
    try:
        # Run behave command and capture output
        result = subprocess.run(
            ["behave"], capture_output=True, text=True
        )
        return jsonify({
            "success": True,
            "output": result.stdout
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
		

