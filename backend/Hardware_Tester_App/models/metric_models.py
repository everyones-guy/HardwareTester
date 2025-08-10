# models/metric_models.py

from sqlalchemy import Column, Integer, String
from Hardware_Tester_App.extensions import db
from datetime import datetime

class Metric(db.Model):
    __tablename__ = 'metrics'
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    peripheral_id = db.Column(db.Integer, db.ForeignKey('public.peripherals.id'), nullable=False)
    metric_type = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    peripheral = db.relationship('Peripheral', backref=db.backref('metrics', lazy=True))

    def __repr__(self):
        return f"<Metric {self.metric_type} Value={self.value}>"
