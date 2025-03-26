import os
import pytest
from flask import url_for
from HardwareTester import create_app, db
from Hardware_Tester_App.models import Valve, TestPlan

# Fixtures for the test environment
@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def init_data(app):
    """Initialize the database with test data."""
    # Add test valves
    valve1 = Valve(name="Valve A", type="Mixing", api_endpoint="http://example.com/api/v1/valve_a", specifications={})
    valve2 = Valve(name="Valve B", type="Control", api_endpoint=None, specifications={})
    db.session.add(valve1)
    db.session.add(valve2)

    # Add test plans
    test_plan1 = TestPlan(name="Plan A", uploaded_by="User1", steps=[{"Step": 1, "Action": "Open Valve", "Parameter": "50%"}])
    db.session.add(test_plan1)

    db.session.commit()

# Test Cases
def test_dashboard_access(client):
    """Test access to the dashboard."""
    response = client.get(url_for("main.dashboard"))
    assert response.status_code == 200
    assert b"Application Dashboard" in response.data

def test_upload_spec_sheet(client):
    """Test uploading a valid spec sheet."""
    data = {
        "file": (open("tests/files/test_spec_sheet.pdf", "rb"), "test_spec_sheet.pdf"),
        "valve_id": 1
    }
    response = client.post(url_for("main.upload_spec_sheet"), data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert b"uploaded successfully" in response.data

def test_upload_spec_sheet_invalid_file_type(client):
    """Test uploading an invalid spec sheet file type."""
    data = {
        "file": (open("tests/files/test_invalid_file.txt", "rb"), "test_invalid_file.txt"),
        "valve_id": 1
    }
    response = client.post(url_for("main.upload_spec_sheet"), data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"File type not allowed" in response.data

def test_get_valves(client, init_data):
    """Test retrieving the list of valves."""
    response = client.get(url_for("main.get_valves"))
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert len(json_data["valves"]) == 2
    assert json_data["valves"][0]["name"] == "Valve A"

def test_run_test_plan(client, init_data):
    """Test running a valid test plan."""
    response = client.post(url_for("main.run_test_plan", test_plan_id=1))
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "results" in json_data

def test_run_test_plan_invalid_id(client):
    """Test running a test plan with an invalid ID."""
    response = client.post(url_for("main.run_test_plan", test_plan_id=999))
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["success"] is False
    assert b"Test plan not found" in response.data

def test_upload_test_plan(client):
    """Test uploading a valid test plan."""
    data = {
        "file": (open("tests/files/test_plan.pdf", "rb"), "test_plan.pdf")
    }
    response = client.post(url_for("main.upload_test_plan"), data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert b"uploaded successfully" in response.data

def test_upload_test_plan_invalid_file_type(client):
    """Test uploading an invalid test plan file type."""
    data = {
        "file": (open("tests/files/test_invalid_plan.doc", "rb"), "test_invalid_plan.doc")
    }
    response = client.post(url_for("main.upload_test_plan"), data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"File type not allowed" in response.data

def test_get_uploaded_test_plans(client, init_data):
    """Test retrieving uploaded test plans."""
    response = client.get(url_for("main.get_uploaded_test_plans"))
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert len(json_data["testPlans"]) == 1
    assert json_data["testPlans"][0]["name"] == "Plan A"

