from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from HardwareTester.extensions import db
from datetime import datetime


class Device(db.Model):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    firmware_version = Column(String(50), nullable=True)
    device_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Device {self.name} (ID={self.device_id})>"


class Peripheral(db.Model):
    __tablename__ = "peripherals"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    properties = Column(JSON, nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)

    device = db.relationship("Device", backref=db.backref("peripherals", lazy="dynamic"))

    def __repr__(self):
        return f"<Peripheral {self.name} (Type={self.type})>"


class Controller(db.Model):
    __tablename__ = "controllers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    firmware_version = Column(String(50), nullable=True)
    device_metadata = Column(JSON, nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)

    device = db.relationship("Device", backref=db.backref("controllers", lazy="dynamic"))

    def __repr__(self):
        return f"<Controller {self.name} Firmware={self.firmware_version}>"


class Emulation(db.Model):
    __tablename__ = "emulations"
    id = Column(Integer, primary_key=True)
    controller_id = Column(Integer, ForeignKey("controllers.id"), nullable=False, index=True)
    status = Column(String(50), default="running", nullable=False)
    logs = Column(Text, nullable=True)
    machine_name = Column(String(255), nullable=False, index=True)
    blueprint = Column(String(255), nullable=False)
    stress_test = Column(Boolean, default=False)
    start_time = Column(DateTime, default=datetime.utcnow)

    controller = db.relationship("Controller", backref=db.backref("emulations", lazy="dynamic"))

    def __repr__(self):
        return f"<Emulation {self.machine_name} (Controller={self.controller.name}) Status={self.status}>"


class Blueprint(db.Model):
    __tablename__ = "blueprints"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Blueprint {self.name}>"
