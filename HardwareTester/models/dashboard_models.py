# models/dashboard_models.py
from sqlalchemy import Column, Integer, String
from HardwareTester.extensions import db

class DashboardData(db.Model):
    __tablename__ = 'dashboard_data'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    value = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<DashboardData {self.name}: {self.value}>"

