from . import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configurations.id'), nullable=False)

    configuration = db.relationship('Configuration', backref=db.backref('projects', lazy=True))

    def __repr__(self):
        return f"<Project {self.name}>"

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='pending', nullable=False)

    project = db.relationship('Project', backref=db.backref('milestones', lazy=True))

    def __repr__(self):
        return f"<Milestone {self.name} for Project {self.project.name}>"
