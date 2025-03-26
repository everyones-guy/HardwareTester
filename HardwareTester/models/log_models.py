# models/log_models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from HardwareTester.extensions import db
from datetime import datetime


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship("User", backref=db.backref("activity_logs", lazy="dynamic"))

    def __repr__(self):
        return f"<ActivityLog {self.action} by User {self.user_id}>"


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))

    def __repr__(self):
        return f"<Notification {self.message} for User {self.user_id or 'All'}>"
