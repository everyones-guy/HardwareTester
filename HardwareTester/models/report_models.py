# models/report_models.py

from sqlalchemy import Column, Integer, String
from HardwareTester.models.db import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")

    user = db.relationship('User', backref=db.backref('reports', lazy='dynamic'))

    def __repr__(self):
        return f"<Report {self.title} by User {self.created_by}>"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'file_path': self.file_path,
            'status': self.status,
        }
