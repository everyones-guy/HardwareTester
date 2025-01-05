import os
import pytest
from HardwareTester import create_app, db

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        yield app

def test_database_initialization(app):
    """Test if the database initializes properly."""
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    # Ensure the database doesn't exist at first
    if os.path.exists(db_path):
        os.remove(db_path)

    # Initialize the database
    with app.app_context():
        db.create_all()

    # Check if the database file was created
    assert os.path.exists(db_path)

def test_missing_database_handling(app):
    """Test if the app gracefully handles a missing database."""
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)

    with app.app_context():
        try:
            db.session.execute("SELECT 1")
        except Exception as e:
            assert "no such table" in str(e)
