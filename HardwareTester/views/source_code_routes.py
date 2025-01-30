import os
import logging
from flask import Blueprint, request, jsonify
from HardwareTester.utils.source_code_analyzer import SourceCodeAnalyzer

source_code_bp = Blueprint("source_code", __name__)

# Set up logging
logger = logging.getLogger("SourceCodeAnalyzer")

# Just initialize `SourceCodeAnalyzer` normally now (it will load languages itself)
analyzer = SourceCodeAnalyzer()

@source_code_bp.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.json
    file_path = data.get("file_path")
    language = data.get("language")

    # Log the request
    logger.info(f"Received analysis request: file={file_path}, language={language}")

    # Validate input parameters
    if not file_path or not language:
        return jsonify({"error": "Missing file_path or language"}), 400

    if language not in analyzer.languages:
        return jsonify({"error": f"Unsupported language: {language}"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 404

    try:
        result = analyzer.parse_file(file_path, language)
        logger.info(f"Successfully analyzed {file_path} ({language})")
        return jsonify({"status": "success", "results": result.sexp()})
    except Exception as e:
        logger.error(f" Error analyzing file {file_path}: {e}")
        return jsonify({"error": "Failed to analyze the file", "details": str(e)}), 500
