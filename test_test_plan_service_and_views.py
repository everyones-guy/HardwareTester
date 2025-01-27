import pytest
from flask import Flask
from flask_login import current_user
from unittest.mock import MagicMock, patch
from io import BytesIO
from HardwareTester.models.test_models import TestPlan, TestStep
from HardwareTester.services.test_plan_service import TestPlanService
from HardwareTester.views.test_plan_views import test_plan_bp

# Mock application and database for testing
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(test_plan_bp)
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True  # Disable login for testing
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

# Test: Upload Test Plan
def test_upload_test_plan(client):
    with patch("HardwareTester.services.test_plan_service.TestPlan.query") as mock_query:
        mock_file = BytesIO(b"Test Plan Content")
        mock_file.filename = "test_plan.txt"

        with client:
            response = client.post(
                "/test-plans/upload",
                data={"file": mock_file, "uploaded_by": "test_user"},
                content_type="multipart/form-data",
            )
        assert response.status_code == 200
        assert response.json["success"] is True

# Test: Run Test Plan
def test_run_test_plan(client):
    with patch("HardwareTester.services.test_plan_service.TestPlan.query.get") as mock_get:
        mock_get.return_value = TestPlan(id=1, name="Mock Test Plan", steps=[])
        with client:
            response = client.post("/test-plans/1/run")
        assert response.status_code == 200
        assert response.json["success"] is True

# Test: Preview Test Plan
def test_preview_test_plan(client):
    with patch("HardwareTester.services.test_plan_service.TestPlan.query.get") as mock_get:
        mock_get.return_value = TestPlan(id=1, name="Mock Test Plan", steps=[
            TestStep(action="Mock Action", parameter="Mock Parameter")
        ])
        with client:
            response = client.get("/test-plans/1/preview")
        assert response.status_code == 200
        assert response.json["success"] is True
        assert "steps" in response.json["plan"]

# Test: List Test Plans
def test_list_test_plans(client):
    with patch("HardwareTester.services.test_plan_service.TestPlan.query.paginate") as mock_paginate:
        mock_paginate.return_value.items = [
            TestPlan(id=1, name="Mock Test Plan", description="Mock Description")
        ]
        mock_paginate.return_value.total = 1
        with client:
            response = client.get("/test-plans/list")
        assert response.status_code == 200
        assert response.json["success"] is True
        assert len(response.json["testPlans"]) > 0

# Test: Create Test Plan
def test_create_test_plan(client):
    with patch("HardwareTester.services.test_plan_service.TestPlan.query") as mock_query:
        with patch("HardwareTester.services.test_plan_service.db.session.commit") as mock_commit:
            with client:
                response = client.post(
                    "/test-plans/create",
                    json={"name": "New Test Plan", "description": "Description"},
                )
            assert response.status_code == 200
            assert response.json["success"] is True
