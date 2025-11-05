"""
Task model for to-do items with smart entity linking
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base

# Association tables for many-to-many relationships
task_profiles = Table(
    'task_profiles',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True)
)

task_companies = Table(
    'task_companies',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('company_id', Integer, ForeignKey('companies.id', ondelete='CASCADE'), primary_key=True)
)

task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Task(Base):
    """Task model for to-do items with automatic entity linking"""

    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Task details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='pending', index=True)  # pending, in_progress, completed, cancelled
    priority = Column(String(50), default='medium', index=True)  # low, medium, high, urgent

    # Dates
    due_date = Column(DateTime, index=True)
    completed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Many-to-many relationships
    profiles = relationship('Profile', secondary=task_profiles, backref='tasks')
    companies = relationship('Company', secondary=task_companies, backref='tasks')
    tags = relationship('Tag', secondary=task_tags, backref='tasks')

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title[:30]}...', status='{self.status}')>"

    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_relations:
            data['profiles'] = [{'id': p.id, 'name': p.name} for p in self.profiles]
            data['companies'] = [{'id': c.id, 'name': c.name} for c in self.companies]
            data['tags'] = [{'id': t.id, 'name': t.name} for t in self.tags]

        return data

    def complete(self):
        """Mark task as completed and update all related goals' progress"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self._update_related_goals()

    def update_status(self, new_status: str):
        """Update task status and refresh related goals' progress"""
        old_status = self.status
        self.status = new_status

        if new_status == 'completed' and old_status != 'completed':
            self.completed_at = datetime.utcnow()

        # Update goals if status changed to/from completed
        if (old_status == 'completed' or new_status == 'completed') and old_status != new_status:
            self._update_related_goals()

    def _update_related_goals(self):
        """Update progress for all goals linked to this task"""
        if hasattr(self, 'goals') and self.goals:
            for goal in self.goals:
                goal.update_progress()

    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return (self.status not in ['completed', 'cancelled'] and
                self.due_date and
                self.due_date < datetime.utcnow())
