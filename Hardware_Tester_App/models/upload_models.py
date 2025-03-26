# models/upload_models.py

from Hardware_Tester_App.extensions import db
from datetime import datetime

class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)