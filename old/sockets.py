from flask_socketio import SocketIO, emit

socketio = SocketIO()

@socketio.on("connect")
def handle_connect():
    emit("log_message", {"message": "Connected to dashboard"})

def log_to_dashboard(message):
    """Emit a real-time log message to the dashboard."""
    socketio.emit("log_message", {"message": message}, broadcast=True)
