"""
Goal model for high-level objectives with smart entity linking and task aggregation
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base

# Association tables for many-to-many relationships
goal_profiles = Table(
    'goal_profiles',
    Base.metadata,
    Column('goal_id', Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True),
    Column('profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

goal_companies = Table(
    'goal_companies',
    Base.metadata,
    Column('goal_id', Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True),
    Column('company_id', Integer, ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

goal_tasks = Table(
    'goal_tasks',
    Base.metadata,
    Column('goal_id', Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True),
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

goal_tags = Table(
    'goal_tags',
    Base.metadata,
    Column('goal_id', Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Goal(Base):
    """Goal model for high-level objectives that aggregate multiple tasks"""

    __tablename__ = 'goals'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Goal details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='active', index=True)  # active, completed, on_hold, cancelled
    priority = Column(String(50), default='medium', index=True)  # low, medium, high, urgent

    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 100.0 percentage

    # Dates
    target_date = Column(DateTime, index=True)
    completed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Many-to-many relationships
    profiles = relationship('Profile', secondary=goal_profiles, backref='goals')
    companies = relationship('Company', secondary=goal_companies, backref='goals')
    tasks = relationship('Task', secondary=goal_tasks, backref='goals')
    tags = relationship('Tag', secondary=goal_tags, backref='goals')

    # One-to-many relationships
    reminders = relationship('Reminder', back_populates='goal', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Goal(id={self.id}, title='{self.title[:30]}...', status='{self.status}', progress={self.progress}%)>"

    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'progress': self.progress,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_relations:
            data['profiles'] = [{'id': p.id, 'name': p.name} for p in self.profiles]
            data['companies'] = [{'id': c.id, 'name': c.name} for c in self.companies]
            data['tasks'] = [{'id': t.id, 'title': t.title, 'status': t.status} for t in self.tasks]
            data['tags'] = [{'id': t.id, 'name': t.name} for t in self.tags]

        return data

    def calculate_progress(self):
        """Calculate progress based on related tasks completion"""
        if not self.tasks:
            return 0.0

        completed_tasks = sum(1 for task in self.tasks if task.status == 'completed')
        total_tasks = len(self.tasks)

        if total_tasks == 0:
            return 0.0

        return round((completed_tasks / total_tasks) * 100, 2)

    def update_progress(self):
        """Update progress and auto-complete if all tasks are done"""
        self.progress = self.calculate_progress()

        # Auto-complete goal if all tasks are completed
        if self.progress == 100.0 and self.status == 'active':
            self.complete()

    def complete(self):
        """Mark goal as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 100.0

    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        if not self.target_date or self.status in ['completed', 'cancelled']:
            return False
        return self.target_date < datetime.utcnow()

    def get_summary(self) -> dict:
        """Get a summary of the goal's status"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks if task.status == 'completed')
        in_progress_tasks = sum(1 for task in self.tasks if task.status == 'in_progress')
        pending_tasks = sum(1 for task in self.tasks if task.status == 'pending')

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'pending_tasks': pending_tasks,
            'total_profiles': len(self.profiles),
            'total_companies': len(self.companies),
            'total_tags': len(self.tags),
            'progress': self.progress,
            'is_overdue': self.is_overdue()
        }
