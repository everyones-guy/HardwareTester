
from sqlalchemy.dialects.postgresql import JSON
from HardwareTester.extensions import db

class DynamicConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    properties = db.Column(JSON)  # Store additional dynamic fields
