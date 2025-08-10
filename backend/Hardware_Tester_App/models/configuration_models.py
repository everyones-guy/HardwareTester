from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from Hardware_Tester_App.extensions import db


class Configuration(db.Model):
    __tablename__ = "configurations"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    layout = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)
    modified_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "layout": self.layout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
        }

    def __repr__(self):
        return f"<Configuration {self.name} (ID={self.id})>"


class Settings(db.Model):
    __tablename__ = "settings"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)
    modified_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
        }

    def __repr__(self):
        return f"<Settings {self.key} = {self.value}>"


class GlobalSettings(db.Model):
    __tablename__ = "global_settings"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)
    modified_by = db.Column(db.Integer, db.ForeignKey("public.users.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "modified_by": self.modified_by,
        }

    def __repr__(self):
        return f"<GlobalSettings {self.setting_key} = {self.setting_value}>"


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