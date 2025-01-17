from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from HardwareTester.extensions import db
from datetime import datetime


class Device(db.Model):
    __tablename__ = "devices"
    id = db.Column(Integer, primary_key=True)
    device_id = db.Column(String(255), nullable=False, unique=True, index=True)
    name = db.Column(String(255), nullable=False)
    firmware_version = db.Column(String(50), nullable=True)
    device_metadata = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Device {self.name} (ID={self.device_id})>"


class Peripheral(db.Model):
    __tablename__ = "peripherals"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False)
    type = db.Column(String(255), nullable=False)
    properties = db.Column(JSON, nullable=True)
    device_id = db.Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)

    device = db.relationship("Device", backref=db.backref("peripherals", lazy="dynamic"))
    
    def __repr__(self):
        return f"<Peripheral {self.name} (Type={self.type})>"


class Controller(db.Model):
    __tablename__ = "controllers"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False, unique=True)
    firmware_version = db.Column(String(50), nullable=True)
    device_metadata = db.Column(JSON, nullable=True)
    device_id = db.Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)

    device = db.relationship("Device", backref=db.backref("controllers", lazy="dynamic"))

    def __repr__(self):
        return f"<Controller {self.name} Firmware={self.firmware_version}>"


class Emulation(db.Model):
    __tablename__ = "emulations"
    id = db.Column(Integer, primary_key=True)
    controller_id = db.Column(Integer, ForeignKey("controllers.id"), nullable=False, index=True)
    status = db.Column(String(50), default="running", nullable=False)
    logs = db.Column(Text, nullable=True)
    machine_name = db.Column(String(255), nullable=False, index=True)
    blueprint = db.Column(String(255), nullable=False)
    stress_test = db.Column(Boolean, default=False)
    start_time = db.Column(DateTime, default=datetime.utcnow)

    controller = db.relationship("Controller", backref=db.backref("emulations", lazy="dynamic"))

    def __repr__(self):
        return f"<Emulation {self.machine_name} (Controller={self.controller.name}) Status={self.status}>"


class Blueprint(db.Model):
    __tablename__ = "blueprints"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False, unique=True, index=True)
    description = db.Column(Text, nullable=True)
    configuration = db.Column(JSON, nullable=True)  # JSON configuration details for the blueprint
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, onupdate=datetime.utcnow)  # Automatically updated when modified
    version = db.Column(String(50), nullable=True)  # Optional versioning field for the blueprint
    author = db.Column(String(255), nullable=True)  # Field to track the creator of the blueprint

    def __repr__(self):
        return f"<Blueprint {self.name} (ID={self.id}, Version={self.version})>"

class Firmware(db.Model):
    __tablename__ = "firmwares"
    id = db.Column(Integer, primary_key=True)
    hash = db.Column(String(64), unique=True, nullable=False)
    content = db.Column(Text, nullable=False)
    mdf = db.Column(JSON, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class DeviceFirmwareHistory(db.Model):
    __tablename__ = "device_firmware_history"
    id = db.Column(Integer, primary_key=True)
    device_id = db.Column(Integer, ForeignKey("devices.id"), nullable=False)
    firmware_id = db.Column(Integer, ForeignKey("firmwares.id"), nullable=False)
    uploaded_at = db.Column(DateTime, default=datetime.utcnow)

    device = db.relationship("Device", backref=db.backref("firmware_history", lazy="dynamic"))
    firmware = db.relationship("Firmware")

class Valve(db.Model):
    __tablename__ = "valves"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    specifications = db.Column(db.JSON, nullable=True)
    state = db.Column(db.String(50), default="closed", nullable=False)  # New field for state
