from Hardware_Tester_App.extensions import db

class Link(db.Model):
    __tablename__ = "links"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    device_metadata = db.Column(db.JSON, nullable=True)  # Store optional metadata as JSON

    def __repr__(self):
        return f"<Link(id={self.id}, source_id={self.source_id}, target_id={self.target_id})>"
