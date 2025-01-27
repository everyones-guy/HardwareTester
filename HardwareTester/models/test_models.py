from HardwareTester.extensions import db
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime


class TestPlan(db.Model):
    __tablename__ = "test_plans"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False, unique=True)
    description = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User table
    modified_by = db.Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User table

    # Relationship to TestStep
    steps = db.relationship("TestStep", backref="test_plan", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert the TestPlan instance to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
            "steps": [step.to_dict() for step in self.steps],
        }

    def __repr__(self):
        return f"<TestPlan {self.name}>"


class TestStep(db.Model):
    __tablename__ = "test_steps"

    id = db.Column(Integer, primary_key=True)
    action = db.Column(String(255), nullable=False)
    parameter = db.Column(String(255), nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User table
    modified_by = db.Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User table
    test_plan_id = db.Column(Integer, ForeignKey("test_plans.id"), nullable=False)

    def to_dict(self):
        """Convert the TestStep instance to a dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "parameter": self.parameter,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
        }

    def __repr__(self):
        return f"<TestStep {self.action} - {self.parameter}>"
