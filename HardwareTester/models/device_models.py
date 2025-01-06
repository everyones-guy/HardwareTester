# models/device_models.py
from sqlalchemy import Column, Integer, String
from HardwareTester.extensions import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<Device {self.name} ({self.device_id})>"

class Peripheral(db.Model):
    __tablename__ = 'peripherals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    properties = db.Column(db.JSON, nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)

    device = db.relationship('Device', backref=db.backref('peripherals', lazy=True))

    def __repr__(self):
        return f"<Peripheral {self.name} ({self.type})>"

class Controller(db.Model):
    __tablename__ = 'controllers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_metadata = db.Column(db.JSON, nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)

    device = db.relationship('Device', backref=db.backref('controllers', lazy=True))

    def __repr__(self):
        return f"<Controller {self.name} Firmware={self.firmware_version}>"

class Emulation(db.Model):
    __tablename__ = 'emulations'
    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer, db.ForeignKey('controllers.id'), nullable=False)
    status = db.Column(db.String(50), default='running')
    logs = db.Column(db.Text, nullable=True)

    controller = db.relationship('Controller', backref=db.backref('emulations', lazy=True))

    def __repr__(self):
        return f"<Emulation for Controller {self.controller.name} Status={self.status}>"
