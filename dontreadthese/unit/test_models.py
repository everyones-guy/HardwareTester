import pytest
from sqlalchemy.exc import IntegrityError
from HardwareTester import create_app, db
from HardwareTester.models import Valve, TestPlan, TestResult

# Fixtures for test environment
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
def session(app):
    """Provide a database session for testing."""
    with app.app_context():
        yield db.session

@pytest.fixture
def mock_data(session):
    """Initialize the database with mock data."""
    # Add valves
    valve1 = Valve(name="Valve A", type="Mixing", api_endpoint="http://example.com/api/v1/valve_a", specifications={"pressure": 150})
    valve2 = Valve(name="Valve B", type="Control", api_endpoint=None, specifications={})
    session.add_all([valve1, valve2])

    # Add test plans
    test_plan = TestPlan(
        name="Test Plan A",
        uploaded_by="User1",
        steps=[
            {"Step": 1, "Action": "Open Valve", "Parameter": "50%"},
            {"Step": 2, "Action": "Close Valve", "Parameter": "0%"}
        ]
    )
    session.add(test_plan)

    # Commit to database
    session.commit()

    return {"valve1": valve1, "valve2": valve2, "test_plan": test_plan}

# Test cases

def test_valve_creation(session):
    """Test creating a new valve."""
    valve = Valve(name="Valve C", type="Mixing", api_endpoint=None, specifications={"temperature": 75})
    session.add(valve)
    session.commit()

    retrieved_valve = Valve.query.filter_by(name="Valve C").first()
    assert retrieved_valve is not None
    assert retrieved_valve.type == "Mixing"
    assert retrieved_valve.specifications["temperature"] == 75

def test_valve_constraints(session):
    """Test constraints on the Valve model."""
    # Test missing name
    valve = Valve(name=None, type="Mixing")
    session.add(valve)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

    # Test missing type
    valve = Valve(name="Valve D", type=None)
    session.add(valve)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

def test_test_plan_creation(mock_data, session):
    """Test creating a new test plan."""
    test_plan = TestPlan(
        name="Test Plan B",
        uploaded_by="User2",
        steps=[
            {"Step": 1, "Action": "Start Pump", "Parameter": "ON"},
            {"Step": 2, "Action": "Stop Pump", "Parameter": "OFF"}
        ]
    )
    session.add(test_plan)
    session.commit()

    retrieved_plan = TestPlan.query.filter_by(name="Test Plan B").first()
    assert retrieved_plan is not None
    assert retrieved_plan.uploaded_by == "User2"
    assert len(retrieved_plan.steps) == 2
    assert retrieved_plan.steps[0]["Action"] == "Start Pump"

def test_test_plan_constraints(session):
    """Test constraints on the TestPlan model."""
    # Test missing name
    test_plan = TestPlan(name=None, uploaded_by="User3")
    session.add(test_plan)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

    # Test missing steps
    test_plan = TestPlan(name="Test Plan C", uploaded_by="User3", steps=None)
    session.add(test_plan)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

def test_test_result_creation(mock_data, session):
    """Test creating a new test result."""
    valve = mock_data["valve1"]
    test_plan = mock_data["test_plan"]

    test_result = TestResult(
        valve_id=valve.id,
        test_plan_id=test_plan.id,
        status=True,
        logs="Test completed successfully."
    )
    session.add(test_result)
    session.commit()

    retrieved_result = TestResult.query.filter_by(valve_id=valve.id).first()
    assert retrieved_result is not None
    assert retrieved_result.status is True
    assert "Test completed successfully" in retrieved_result.logs

def test_test_result_constraints(session):
    """Test constraints on the TestResult model."""
    # Test missing valve_id
    test_result = TestResult(valve_id=None, test_plan_id=1, status=True, logs="Log data")
    session.add(test_result)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

    # Test missing test_plan_id
    test_result = TestResult(valve_id=1, test_plan_id=None, status=True, logs="Log data")
    session.add(test_result)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()

    # Test missing status
    test_result = TestResult(valve_id=1, test_plan_id=1, status=None, logs="Log data")
    session.add(test_result)
    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()
