from sqlalchemy import Column, Integer, String
from HardwareTester.extensions import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('public.configurations.id'), nullable=False)

    configuration = db.relationship('Configuration', backref=db.backref('projects', lazy=True, cascade="all, delete-orphan"))
                                    
    def __repr__(self):
        return f"<Project {self.name}>"

class Milestone(db.Model):
    __tablename__ = 'milestones'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('public.projects.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    VALID_STATUSES = ['pending', 'completed', 'in_progress']
    
    project = db.relationship('Project', backref=db.backref('milestones', lazy=True))

    def set_status(self, status):
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        self.status = status


    def __repr__(self):
        return f"<Milestone {self.name} for Project {self.project.name}>"

