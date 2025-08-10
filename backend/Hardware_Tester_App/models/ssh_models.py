from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from Hardware_Tester_App.extensions import db
from Hardware_Tester_App.utils.bcrypt_utils import hash_password, check_password


class SSHConnection(db.Model):
    __tablename__ = "ssh_connections"
    __table_args__ = {'schema': 'public'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, default=22, nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Store hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def set_password(self, password):
        """
        Hash and set the password for the SSH connection.
        """
        if not password:
            raise ValueError("Password cannot be empty.")
        self.password_hash = hash_password(password)

    def check_password(self, password):
        """
        Validate the provided password against the stored hash.
        """
        return check_password(password, self.password_hash)

    def __repr__(self):
        return f"<SSHConnection {self.name} (Host={self.host}, Port={self.port})>"
