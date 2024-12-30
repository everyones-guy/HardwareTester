from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

# Initialize SQLAlchemy
db = SQLAlchemy()

# Enums for Roles and Access Levels
class UserRole(Enum):
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'

class AccessLevel(Enum):
    READ = 'read'
    WRITE = 'write'
    EXECUTE = 'execute'
    FULL = 'full'

# Mixins
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Models
class User(UserMixin, db.Model, TimestampMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def __repr__(self):
        return f"<User {self.username}>"

class Role(db.Model, TimestampMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    access_level = db.Column(db.Enum(AccessLevel), default=AccessLevel.READ, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"

class Configuration(db.Model, TimestampMixin):
    __tablename__ = 'configurations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    layout = db.Column(db.JSON, nullable=False)  # JSON layout for valves and peripherals

    def __repr__(self):
        return f"<Configuration {self.name}>"

class Device(db.Model, TimestampMixin):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    firmware_version = db.Column(db.String(50), nullable=True)  # Firmware version
    device_metadata = db.Column(db.JSON, nullable=True)  # Metadata about the device

    def __repr__(self):
        return f"<Device {self.name} ({self.device_id})>"

class Peripheral(db.Model, TimestampMixin):
    __tablename__ = 'peripherals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)  # Sensor, Actuator, etc.
    properties = db.Column(db.JSON, nullable=True)  # Dynamic properties (e.g., temperature, pressure)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)

    device = db.relationship('Device', backref=db.backref('peripherals', lazy=True))

    def __repr__(self):
        return f"<Peripheral {self.name} ({self.type})>"

class Metric(db.Model, TimestampMixin):
    __tablename__ = 'metrics'

    id = db.Column(db.Integer, primary_key=True)
    peripheral_id = db.Column(db.Integer, db.ForeignKey('peripherals.id'), nullable=False)
    metric_type = db.Column(db.String(100), nullable=False)  # Temperature, Pressure, etc.
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    peripheral = db.relationship('Peripheral', backref=db.backref('metrics', lazy=True))

    def __repr__(self):
        return f"<Metric {self.metric_type} Value={self.value}>"

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __repr__(self):
        return f"<ActivityLog {self.action} by User {self.user_id}>"

class Token(db.Model):
    __tablename__ = 'tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref=db.backref('tokens', lazy=True))

    def is_valid(self):
        return datetime.utcnow() < self.expiration

    def __repr__(self):
        return f"<Token {self.token} for User {self.user_id}>"

class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Settings {self.key} = {self.value}>"


class Controller(db.Model, TimestampMixin):
    __tablename__ = 'controllers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)  # Any additional info about the controller
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)

    device = db.relationship('Device', backref=db.backref('controllers', lazy=True))

    def __repr__(self):
        return f"<Controller {self.name} Firmware={self.firmware_version}>"

class Project(db.Model, TimestampMixin):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configurations.id'), nullable=False)

    configuration = db.relationship('Configuration', backref=db.backref('projects', lazy=True))

    def __repr__(self):
        return f"<Project {self.name}>"

class Milestone(db.Model, TimestampMixin):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='pending', nullable=False)  # e.g., pending, completed

    project = db.relationship('Project', backref=db.backref('milestones', lazy=True))

    def __repr__(self):
        return f"<Milestone {self.name} for Project {self.project.name}>"


class Notification(db.Model, TimestampMixin):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null means it's a system-wide notification
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f"<Notification {self.message} for User {self.user_id or 'All'}>"

class Emulation(db.Model, TimestampMixin):
    __tablename__ = 'emulations'

    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer, db.ForeignKey('controllers.id'), nullable=False)
    status = db.Column(db.String(50), default='running')  # running, stopped, etc.
    logs = db.Column(db.Text, nullable=True)

    controller = db.relationship('Controller', backref=db.backref('emulations', lazy=True))

    def __repr__(self):
        return f"<Emulation for Controller {self.controller.name} Status={self.status}>"

class DashboardData(db.Model, TimestampMixin):
    __tablename__ = 'dashboard_data'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)  # e.g., "Active Devices", "Total Tests"
    value = db.Column(db.Integer, nullable=False)  # e.g., 10, 200
    description = db.Column(db.String(500), nullable=True)  # Optional description of the data

    def __repr__(self):
        return f"<DashboardData {self.name}: {self.value}>"

class Report(db.Model, TimestampMixin):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=True)  # Path to the saved report file
    status = db.Column(db.String(50), nullable=False, default="Pending")  # e.g., Pending, Completed, Failed

    # Relationships
    user = db.relationship('User', backref=db.backref('reports', lazy='dynamic'))

    def __repr__(self):
        return f"<Report {self.title} by User {self.created_by}>"

    def to_dict(self):
        """Convert the Report object to a dictionary for easy JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'file_path': self.file_path,
            'status': self.status,
        }

# User settings
class UserSettings(db.Model, TimestampMixin):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    setting_key = db.Column(db.String(255), nullable=False)
    setting_value = db.Column(db.Text, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('settings', lazy='dynamic'))

    def __repr__(self):
        return f"<UserSettings {self.setting_key} for User {self.user_id}>"

    def to_dict(self):
        """Convert the UserSettings object to a dictionary for easy JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
        }

# Global Settings
class GlobalSettings(db.Model, TimestampMixin):
    __tablename__ = 'global_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)  # Optional for documentation

    def __repr__(self):
        return f"<GlobalSettings {self.setting_key}={self.setting_value}>"

    def to_dict(self):
        """Convert the GlobalSettings object to a dictionary for easy JSON serialization."""
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description,
        }
    