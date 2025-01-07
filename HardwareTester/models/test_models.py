from HardwareTester.extensions import db
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime



class TestPlan(db.Model):
    __tablename__ = "test_plans"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False, unique=True)
    description = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to TestStep
    steps = db.relationship("TestStep", backref="test_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestPlan {self.name}>"


class TestStep(db.Model):
    __tablename__ = "test_steps"

    id = db.Column(Integer, primary_key=True)
    action = db.Column(String(255), nullable=False)
    parameter = db.Column(String(255), nullable=True)
    test_plan_id = db.Column(Integer, ForeignKey("test_plans.id"), nullable=False)

    def __repr__(self):
        return f"<TestStep {self.action} - {self.parameter}>"
