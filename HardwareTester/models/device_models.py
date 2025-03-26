from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from datetime import datetime
from HardwareTester.extensions import db


class Device(db.Model):
    __tablename__ = "devices"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    modified_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Device {self.name} (ID={self.device_id})>"


class Peripheral(db.Model):
    __tablename__ = "peripherals"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    properties = db.Column(db.JSON, nullable=True)
    device_id = db.Column(db.Integer, ForeignKey("devices.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    modified_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    device = db.relationship("Device", backref=db.backref("peripherals", lazy="dynamic"))

    def __repr__(self):
        return f"<Peripheral {self.name} (Type={self.type})>"


class Controller(db.Model):
    __tablename__ = "controllers"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)
    device_id = db.Column(db.Integer, ForeignKey("devices.id"), nullable=True, index=True)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    modified_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    device = db.relationship("Device", backref=db.backref("controllers", lazy="dynamic"))

    def __repr__(self):
        return f"<Controller {self.name} Firmware={self.firmware_version}>"


class Emulation(db.Model):
    __tablename__ = "emulations"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    controller_id = db.Column(db.Integer, ForeignKey("controllers.id"), nullable=False, index=True)
    status = db.Column(db.String(50), default="running", nullable=False)
    logs = db.Column(db.Text, nullable=True)
    machine_name = db.Column(db.String(255), nullable=False, index=True)
    blueprint_id = db.Column(db.Integer, ForeignKey("blueprints.id"), nullable=False)
    blueprint = db.relationship("Blueprint", backref=db.backref("emulations", lazy="dynamic"))
    stress_test = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    modified_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    controller = db.relationship("Controller", backref=db.backref("emulations", lazy="dynamic"))

    def __repr__(self):
        return f"<Emulation {self.machine_name} (Controller={self.controller.name}) Status={self.status}>"


class Blueprint(db.Model):
    __tablename__ = "blueprints"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    configuration = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    version = db.Column(db.String(50), nullable=True)
    author = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Blueprint {self.name} (ID={self.id}, Version={self.version})>"


class Firmware(db.Model):
    __tablename__ = "firmwares"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.String(64), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    mdf = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Firmware {self.hash}>"


class DeviceFirmwareHistory(db.Model):
    __tablename__ = "device_firmware_history"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, ForeignKey("devices.id"), nullable=False)
    firmware_id = db.Column(db.Integer, ForeignKey("firmwares.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    device = db.relationship("Device", backref=db.backref("firmware_history", lazy="dynamic"))
    firmware = db.relationship("Firmware")

    def __repr__(self):
        return f"<DeviceFirmwareHistory Device={self.device_id} Firmware={self.firmware_id}>"


class Valve(db.Model):
    __tablename__ = "valves"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    specifications = db.Column(db.JSON, nullable=True)
    state = db.Column(db.String(50), default="closed", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)
    modified_by = db.Column(db.Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Valve {self.name} (Type={self.type}) State={self.state}>"
