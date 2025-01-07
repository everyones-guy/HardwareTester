
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from HardwareTester.extensions import db


class TestPlan(db.Model):
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to TestStep
    steps = relationship("TestStep", backref="test_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestPlan {self.name}>"


class TestStep(db.Model):
    __tablename__ = "test_steps"

    id = Column(Integer, primary_key=True)
    action = Column(String(255), nullable=False)
    parameter = Column(String(255), nullable=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)

    def __repr__(self):
        return f"<TestStep {self.action} - {self.parameter}>"
