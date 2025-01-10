# user_models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum
from HardwareTester.utils.bcrypt_utils import hash_password, check_password
from HardwareTester.extensions import db

class UserRole(Enum):
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return check_password(password, self.password_hash)

    def __repr__(self):
        return f"<User {self.username}>"

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    access_level = db.Column(db.Enum(UserRole), nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"

class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref=db.backref('tokens', lazy=True))

    def is_valid(self):
        return datetime.utcnow() < self.expiration

    def __repr__(self):
        return f"<Token {self.token} for User {self.user_id}>"

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    setting_key = db.Column(db.String(255), nullable=False)
    setting_value = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref=db.backref('settings', lazy='dynamic'))

    def __repr__(self):
        return f"<UserSettings {self.setting_key} for User {self.user_id}>"
   