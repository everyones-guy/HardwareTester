from sqlalchemy import Column, Integer, String
from HardwareTester.extensions import db

class Configuration(db.Model):
    __tablename__ = 'configurations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    layout = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f"<Configuration {self.name}>"

class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Settings {self.key} = {self.value}>"

class GlobalSettings(db.Model):
    __tablename__ = 'global_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<GlobalSettings {self.setting_key}={self.setting_value}>"
