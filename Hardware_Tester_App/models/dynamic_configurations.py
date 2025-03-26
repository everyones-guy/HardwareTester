from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, Text
from datetime import datetime
from HardwareTester.extensions import db

class DynamicConfiguration(db.Model):
    __tablename__ = "dynamic_configurations"
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    properties = db.Column(db.JSON, nullable=True)  # Store additional dynamic fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)  # Link to User table
    modified_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)  # Link to User table

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
        }

    def __repr__(self):
        return (
            f"<DynamicConfiguration(id={self.id}, type={self.type}, name={self.name}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )
