from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# User Roles Enum
from enum import Enum

class UserRole(Enum):
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Valve(db.Model, TimestampMixin):
    __tablename__ = "valves"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.String(255), nullable=False)
    api_endpoint = db.Column(db.Text, nullable=True)
    specifications = db.Column(db.JSON, nullable=True)
    spec_sheet_path = db.Column(db.String(255), nullable=True)  # Path to the spec sheet file

    def __repr__(self):
        return f"<Valve {self.name} ({self.type})>"


class TestPlan(db.Model, TimestampMixin):
    __tablename__ = "test_plans"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    uploaded_by = db.Column(db.String(255), nullable=False)
    steps = db.Column(db.JSON, nullable=False)  # Store parsed steps as JSON

    def __repr__(self):
        return f"<TestPlan {self.name}>"


class TestResult(db.Model, TimestampMixin):
    __tablename__ = "test_results"
    id = db.Column(db.Integer, primary_key=True)
    valve_id = db.Column(db.Integer, db.ForeignKey("valves.id"), nullable=False)
    test_plan_id = db.Column(db.Integer, db.ForeignKey("test_plans.id"), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    logs = db.Column(db.Text, nullable=True)

    valve = db.relationship("Valve", backref="test_results")  # Optional for easier access
    test_plan = db.relationship("TestPlan", backref="test_results")

    def __repr__(self):
        return f"<TestResult Valve {self.valve_id} Plan {self.test_plan_id} Status {'Pass' if self.status else 'Fail'}>"


# User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def __repr__(self):
        return f"<User {self.username}>"


class Configuration(db.Model, TimestampMixin):
    __tablename__ = "configurations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    layout = db.Column(db.JSON, nullable=False)  # JSON layout for valves and peripherals

    def __repr__(self):
        return f"<Configuration {self.name}>"


class Device(db.Model, TimestampMixin):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    device_metadata = db.Column(db.JSON, nullable=True)  # Device metadata
    settings = db.Column(db.JSON, nullable=True)  # Device settings and submenus
    firmware_version = db.Column(db.String(50), nullable=True)  # Firmware version

    def __repr__(self):
        return f"<Device {self.device_id} ({self.name})>"


class Peripheral(db.Model, TimestampMixin):
    __tablename__ = "peripherals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)  # e.g., Sensor, Actuator
    properties = db.Column(db.JSON, nullable=False)  # Dynamic properties (e.g., temperature, pressure)
    parent_device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True)

    parent_device = db.relationship("Device", backref="peripherals")

    def __repr__(self):
        return f"<Peripheral {self.name} ({self.type})>"


class Metric(db.Model, TimestampMixin):
    __tablename__ = "metrics"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    peripheral_id = db.Column(db.Integer, db.ForeignKey("peripherals.id"), nullable=True)
    metric_type = db.Column(db.String(255), nullable=False)  # e.g., Temperature, Pressure
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    device = db.relationship("Device", backref="metrics")
    peripheral = db.relationship("Peripheral", backref="metrics")

    def __repr__(self):
        return f"<Metric {self.metric_type} Value={self.value}>"


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

    def __repr__(self):
        return f"<Post {self.title} by {self.author.username}>"
    
# Token Model for Password Reset or Email Confirmation
class Token(db.Model):
    __tablename__ = 'tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(200), unique=True, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('tokens', lazy=True))

    def is_valid(self):
        return datetime.utcnow() < self.expiration

    def __repr__(self):
        return f"<Token {self.token} for {self.user.username}>"

# Activity Log Model for User Actions
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.user.username}>"
    
# Settings Model for storing application settings
class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Settings {self.key}: {self.value}>"