# dashboard_models.py

from Hardware_Tester_App.extensions import db
from datetime import datetime

class DashboardData(db.Model):
    __tablename__ = 'dashboard_data'
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=False)  # Foreign key to User table
    name = db.Column(db.String(255), nullable=False, unique=True)
    value = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=True, default=None)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "value": self.value,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<DashboardData(id={self.id}, user_id={self.user_id}, title={self.title}, type={self.type})>"
