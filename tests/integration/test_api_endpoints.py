import pytest
from HardwareTester import create_app

@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client

def test_get_system_info(client):
    """Test the /get-system-info endpoint."""
    response = client.get("/get-system-info")
    assert response.status_code == 200
    data = response.get_json()
    assert "Platform" in data["info"]
    assert "Memory (GB)" in data["info"]
