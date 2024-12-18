from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

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
    valve_id = db.Column(db.Integer, db.ForeignKey('valves.id'), nullable=False)
    test_plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    logs = db.Column(db.Text, nullable=True)

    valve = db.relationship("Valve", backref="test_results")  # Optional for easier access
    test_plan = db.relationship("TestPlan", backref="test_results")

    def __repr__(self):
        return f"<TestResult Valve {self.valve_id} Plan {self.test_plan_id} Status {'Pass' if self.status else 'Fail'}>"

class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)  # Store hashed password
    email = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f"<User {self.username}>"

class Configuration(db.Model, TimestampMixin):
    __tablename__ = "configurations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    layout = db.Column(db.JSON, nullable=False)  # JSON layout for valves and peripherals

    def __repr__(self):
        return f"<Configuration {self.name}>"
