from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from HardwareTester.extensions import db
from datetime import datetime


class Device(db.Model):
    __tablename__ = "devices"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<Device {self.name} (ID={self.device_id})>"


class Peripheral(db.Model):
    __tablename__ = "peripherals"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    properties = db.Column(db.JSON, nullable=True)
    device_id = db.Column(db.Integer, ForeignKey("devices.id"), nullable=False, index=True)

    device = db.relationship("Device", backref=db.backref("peripherals", lazy="dynamic"))
    
    def __repr__(self):
        return f"<Peripheral {self.name} (Type={self.type})>"


class Controller(db.Model):
    __tablename__ = "controllers"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)
    device_id = db.Column(db.Integer, ForeignKey("devices.id"), nullable=True, index=True)
    available = db.Column(db.Boolean, default=True)  # Add this column


    device = db.relationship("Device", backref=db.backref("controllers", lazy="dynamic"))

    def __repr__(self):
        return f"<Controller {self.name} Firmware={self.firmware_version}>"


class Emulation(db.Model):
    __tablename__ = "emulations"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    controller_id = db.Column(db.Integer, ForeignKey("controllers.id"), nullable=False, index=True)
    status = db.Column(db.String(50), default="running", nullable=False)
    logs = db.Column(db.Text, nullable=True)
    machine_name = db.Column(db.String(255), nullable=False, index=True)
    blueprint_id = db.Column(db.Integer, ForeignKey("blueprints.id"), nullable=False)
    blueprint = db.relationship("Blueprint", backref=db.backref("emulations", lazy="dynamic"))
    stress_test = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)

    controller = db.relationship("Controller", backref=db.backref("emulations", lazy="dynamic"))

    def __repr__(self):
        return f"<Emulation {self.machine_name} (Controller={self.controller.name}) Status={self.status}>"


class Blueprint(db.Model):
    __tablename__ = "blueprints"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    configuration = db.Column(db.JSON, nullable=True)  # JSON configuration details for the blueprint
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    version = db.Column(db.String(50), nullable=True)
    author = db.Column(db.String(255), nullable=True)

    
    def __repr__(self):
        return f"<Blueprint {self.name} (ID={self.id}, Version={self.version})>"

class Firmware(db.Model):
    __tablename__ = "firmwares"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.String(64), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    mdf = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeviceFirmwareHistory(db.Model):
    __tablename__ = "device_firmware_history"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, ForeignKey("devices.id"), nullable=False)
    firmware_id = db.Column(db.Integer, ForeignKey("firmwares.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    device = db.relationship("Device", backref=db.backref("firmware_history", lazy="dynamic"))
    firmware = db.relationship("Firmware")

class Valve(db.Model):
    __tablename__ = "valves"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    specifications = db.Column(db.JSON, nullable=True)
    state = db.Column(db.String(50), default="closed", nullable=False)  # New field for state
