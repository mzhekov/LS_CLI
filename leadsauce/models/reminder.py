"""
Reminder model for tasks and follow-ups
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from leadsauce.utils.db import Base


class Reminder(Base):
    """Reminder model for tasks and follow-ups"""

    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Optional relationships - at least one must be set
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True, index=True)
    goal_id = Column(Integer, ForeignKey('goals.id', ondelete='CASCADE'), nullable=True, index=True)
    parent_reminder_id = Column(Integer, ForeignKey('reminders.id', ondelete='SET NULL'))

    # Reminder details
    title = Column(String(255), nullable=False)
    message = Column(Text)
    reminder_date = Column(DateTime, nullable=False, index=True)
    priority = Column(String(50), default='medium', index=True)  # low, medium, high
    category = Column(String(50), default='general', index=True)  # call, email, meeting, follow-up, birthday, general

    # Status
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime)
    completion_note = Column(Text)
    notification_sent = Column(Boolean, default=False)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50))  # daily, weekly, monthly, yearly

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship('Profile', back_populates='reminders')
    company = relationship('Company', back_populates='reminders')
    task = relationship('Task', back_populates='reminders')
    goal = relationship('Goal', back_populates='reminders')
    parent_reminder = relationship('Reminder', remote_side=[id], backref='child_reminders')

    def __repr__(self):
        return f"<Reminder(id={self.id}, title='{self.title}')>"

    def get_linked_entity_info(self):
        """Get information about the linked entity"""
        if self.profile:
            return ('profile', self.profile.name, self.profile.id)
        elif self.company:
            return ('company', self.company.name, self.company.id)
        elif self.task:
            return ('task', self.task.title, self.task.id)
        elif self.goal:
            return ('goal', self.goal.title, self.goal.id)
        else:
            return (None, None, None)

    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'profile_id': self.profile_id,
            'company_id': self.company_id,
            'task_id': self.task_id,
            'goal_id': self.goal_id,
            'parent_reminder_id': self.parent_reminder_id,
            'title': self.title,
            'message': self.message,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'priority': self.priority,
            'category': self.category,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completion_note': self.completion_note,
            'notification_sent': self.notification_sent,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_relations:
            if self.profile:
                data['profile'] = {
                    'id': self.profile.id,
                    'name': self.profile.name,
                    'email': self.profile.email
                }
            if self.company:
                data['company'] = {
                    'id': self.company.id,
                    'name': self.company.name
                }
            if self.task:
                data['task'] = {
                    'id': self.task.id,
                    'title': self.task.title,
                    'status': self.task.status
                }
            if self.goal:
                data['goal'] = {
                    'id': self.goal.id,
                    'title': self.goal.title,
                    'progress': self.goal.progress
                }

        return data

    def complete(self, note: str = None):
        """Mark reminder as completed"""
        self.completed = True
        self.completed_at = datetime.utcnow()
        if note:
            self.completion_note = note

    def is_overdue(self) -> bool:
        """Check if reminder is overdue"""
        return not self.completed and self.reminder_date < datetime.utcnow()
