import pytest
from flask_socketio import SocketIOTestClient
from HardwareTester import create_app, socketio

# Fixtures for test environment
@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app("testing")
    with app.app_context():
        yield app

@pytest.fixture
def socket_client(app):
    """Set up a SocketIO test client."""
    client = socketio.test_client(app)
    yield client
    client.disconnect()

# Test cases

def test_socket_connection(socket_client):
    """Test that the client can successfully connect to the server."""
    assert socket_client.is_connected()
    received = socket_client.get_received()
    assert len(received) == 0  # No messages should be received on connection

def test_socket_disconnect(socket_client):
    """Test that the client can successfully disconnect."""
    socket_client.disconnect()
    assert not socket_client.is_connected()

def test_log_message_event(socket_client):
    """Test sending a 'log_message' event to the server."""
    test_message = "This is a test log message."
    socket_client.emit("log_message", {"message": test_message})
    received = socket_client.get_received()

    # Verify the server echoes the message back
    assert len(received) > 0
    event = received[0]
    assert event["name"] == "log_message"
    assert event["args"][0]["message"] == test_message

def test_custom_event(socket_client):
    """Test a custom SocketIO event."""
    test_data = {"key": "value"}
    socket_client.emit("custom_event", test_data)
    received = socket_client.get_received()

    # Verify the server handles the custom event
    assert len(received) > 0
    event = received[0]
    assert event["name"] == "custom_event_response"
    assert event["args"][0]["status"] == "success"

def test_broadcast_message(socket_client):
    """Test broadcasting a message to all clients."""
    broadcast_message = "Broadcasting to all clients."
    socketio.emit("broadcast", {"message": broadcast_message})
    received = socket_client.get_received()

    # Verify the client received the broadcast
    assert len(received) > 0
    event = received[0]
    assert event["name"] == "broadcast"
    assert event["args"][0]["message"] == broadcast_message

def test_invalid_event(socket_client):
    """Test handling an invalid event."""
    socket_client.emit("invalid_event", {"data": "test"})
    received = socket_client.get_received()

    # Verify the server does not crash and provides appropriate feedback
    assert len(received) == 0  # Invalid events should not generate responses
