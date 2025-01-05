# models/metric_models.py

from . import db
from datetime import datetime

class Metric(db.Model):
    __tablename__ = 'metrics'
    id = db.Column(db.Integer, primary_key=True)
    peripheral_id = db.Column(db.Integer, db.ForeignKey('peripherals.id'), nullable=False)
    metric_type = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    peripheral = db.relationship('Peripheral', backref=db.backref('metrics', lazy=True))

    def __repr__(self):
        return f"<Metric {self.metric_type} Value={self.value}>"
