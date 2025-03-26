import pytest
from Hardware_Tester_App.utils.api_manager import APIManager

@pytest.fixture
def api_manager():
    return APIManager(base_url="https://jsonplaceholder.typicode.com")

def test_get_request(api_manager):
    response = api_manager.get("posts/1")
    assert "userId" in response

def test_post_request(api_manager):
    new_post = {"title": "foo", "body": "bar", "userId": 1}
    response = api_manager.post("posts", payload=new_post)
    assert response.get("id") is not None

def test_connection(api_manager):
    status = api_manager.test_connection()
    assert status["status"] == "connected"
