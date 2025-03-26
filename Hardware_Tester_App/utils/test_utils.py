import pytest
from io import BytesIO
from HardwareTester.utils.parsers import parse_text, parse_csv, parse_pdf, parse_file
from HardwareTester.utils.validators import (
    allowed_file,
    validate_file_upload,
    validate_test_plan_steps,
    validate_valve_id,
    validate_json,
)

# Fixtures for mock data
@pytest.fixture
def mock_test_plan():
    """Mock test plan data."""
    return [
        {"Step": 1, "Action": "Open Valve", "Parameter": "50%"},
        {"Step": 2, "Action": "Close Valve", "Parameter": "0%"},
    ]

@pytest.fixture
def mock_spec_sheet():
    """Mock spec sheet content."""
    return "Valve Specifications: \n Type: Mixing \n Pressure: 150 PSI"

@pytest.fixture
def mock_json():
    """Mock JSON object."""
    return {"name": "Valve A", "type": "Mixing", "specifications": {"pressure": 150}}

# Test: allowed_file
def test_allowed_file():
    assert allowed_file("example.pdf", {"pdf", "docx"}) is True
    assert allowed_file("example.txt", {"pdf", "docx"}) is False
    assert allowed_file("example", {"pdf", "docx"}) is False

# Test: validate_file_upload
def test_validate_file_upload():
    valid_file = BytesIO(b"Test Content")
    valid_file.filename = "example.pdf"
    valid_file.seek(0, 2)  # Move to end of file to simulate size
    valid_file_size_mb = valid_file.tell() / (1024 * 1024)  # Size in MB
    valid_file.seek(0)  # Reset file pointer

    # Valid case
    result, message = validate_file_upload(valid_file, {"pdf", "docx"}, 16)
    assert result is True
    assert message == "File is valid."

    # Invalid file type
    valid_file.filename = "example.txt"
    result, message = validate_file_upload(valid_file, {"pdf", "docx"}, 16)
    assert result is False
    assert "File type not allowed" in message

    # Exceeding size
    large_file = BytesIO(b"A" * (17 * 1024 * 1024))  # 17 MB file
    large_file.filename = "large_example.pdf"
    result, message = validate_file_upload(large_file, {"pdf", "docx"}, 16)
    assert result is False
    assert "File size exceeds" in message

# Test: validate_test_plan_steps
def test_validate_test_plan_steps(mock_test_plan):
    # Valid steps
    result, message = validate_test_plan_steps(mock_test_plan)
    assert result is True
    assert message == "Test plan steps are valid."

    # Invalid step structure
    invalid_plan = [{"Step": 1, "Action": "Open Valve"}]  # Missing "Parameter"
    result, message = validate_test_plan_steps(invalid_plan)
    assert result is False
    assert "missing required keys" in message

# Test: validate_valve_id
def test_validate_valve_id():
    assert validate_valve_id(123) == (True, "Valve ID is valid.")
    assert validate_valve_id(-1) == (False, "Valve ID must be a positive integer.")
    assert validate_valve_id(None) == (False, "Valve ID cannot be empty.")

# Test: validate_json
def test_validate_json(mock_json):
    required_keys = ["name", "type", "specifications"]
    result, message = validate_json(mock_json, required_keys)
    assert result is True
    assert message == "JSON object is valid."

    # Missing keys
    incomplete_json = {"name": "Valve A", "type": "Mixing"}
    result, message = validate_json(incomplete_json, required_keys)
    assert result is False
    assert "Missing required keys" in message

# Test: parse_test_plan
def test_parse_test_plan(mock_test_plan):
    # Mock test plan file
    test_plan_content = "Step: 1, Action: Open Valve, Parameter: 50%\nStep: 2, Action: Close Valve, Parameter: 0%"
    test_plan_file = BytesIO(test_plan_content.encode("utf-8"))

    # Parse test plan
    parsed_steps = test_parse_test_plan(test_plan_file)
    assert parsed_steps == mock_test_plan

    # Invalid content
    invalid_content = BytesIO(b"Invalid content")
    with pytest.raises(ValueError):
        test_parse_test_plan(invalid_content)

# Test: parse_spec_sheet
def test_parse_spec_sheet(mock_spec_sheet):
    # Mock spec sheet file
    spec_sheet_file = BytesIO(mock_spec_sheet.encode("utf-8"))
    parsed_data = test_parse_spec_sheet(spec_sheet_file)
    assert "Valve Specifications" in parsed_data
    assert "Pressure: 150 PSI" in parsed_data

    # Invalid content
    invalid_spec_sheet = BytesIO(b"")
    with pytest.raises(ValueError):
        test_parse_spec_sheet(invalid_spec_sheet)

