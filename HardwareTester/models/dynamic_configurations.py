from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from HardwareTester.extensions import db

class DynamicConfiguration(db.Model):
    __tablename__ = "dynamic_configurations"
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    properties = Column(JSON, nullable=True)  # Store additional dynamic fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User table
    modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User table

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
