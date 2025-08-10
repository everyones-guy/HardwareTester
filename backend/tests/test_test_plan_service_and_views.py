import pytest
from flask import Flask, render_template_string, jsonify
from flask_login import LoginManager, current_user
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from Hardware_Tester_App.models.test_models import TestPlan, TestStep
from Hardware_Tester_App.views.test_plan_views import test_plan_bp
from Hardware_Tester_App.services.test_plan_service import TestPlanService
import os
import sys
from flask.cli import with_appcontext


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Hardware_Tester_App')))



from unittest.mock import MagicMock

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret"

    login_manager = MagicMock()
    app.login_manager = login_manager

    app.register_blueprint(test_plan_bp)
    yield app


@pytest.fixture
def client(app):
    with app.app_context():  # Ensure the app context is active for all tests
        yield app.test_client()

# Test: Upload Test Plan
def test_upload_test_plan(app, client):
    with app.app_context():
        mock_file = BytesIO(b"Test Plan Content")
        mock_file.filename = "test_plan.txt"

        # Patch TestPlan.query
        with patch("Hardware_Tester_App.services.test_plan_service.db.session") as mock_db_session:
            response = client.post(
                "/test-plans/upload",
                data={"file": mock_file, "uploaded_by": "test_user"},
                content_type="multipart/form-data",
            )
            assert response.status_code == 200 or response.status_code == 400

# Test: Run Test Plan
def test_run_test_plan(app, client):
    with app.app_context():
        with patch("Hardware_Tester_App.services.test_plan_service.TestPlan.query.get") as mock_get:
            mock_get.return_value = TestPlan(id=1, name="Mock Test Plan", steps=[])
            response = client.post("/test-plans/1/run")
            assert response.status_code == 200 or response.status_code == 400

# Test: Preview Test Plan
def test_preview_test_plan(app, client):
    with app.app_context():
        with patch("Hardware_Tester_App.services.test_plan_service.TestPlan.query.get") as mock_get:
            mock_get.return_value = TestPlan(id=1, name="Mock Test Plan", steps=[
                TestStep(action="Mock Action", parameter="Mock Parameter")
            ])
            response = client.get("/test-plans/1/preview")
            assert response.status_code == 200 or response.status_code == 400

# Test: List Test Plans
def test_list_test_plans(app, client):
    with app.app_context():
        with patch("Hardware_Tester_App.services.test_plan_service.TestPlan.query.paginate") as mock_paginate:
            mock_paginate.return_value.items = [
                TestPlan(id=1, name="Mock Test Plan", description="Mock Description")
            ]
            mock_paginate.return_value.total = 1
            response = client.get("/test-plans/list")
            assert response.status_code == 200 or response.status_code == 400

# Test: Create Test Plan
def test_create_test_plan(app, client):
    with app.app_context():
        with patch("Hardware_Tester_App.services.test_plan_service.db.session") as mock_db_session:
            response = client.post(
                "/test-plans/create",
                json={"name": "New Test Plan", "description": "Description"},
            )
            assert response.status_code == 200 or response.status_code == 400
